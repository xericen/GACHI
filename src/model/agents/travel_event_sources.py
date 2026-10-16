import datetime
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class EventSources:
    """Bounded requests to official schedule sources; no model-generated dates."""
    def __init__(self, env_value):
        self.env_value = env_value

    def _request(self, url, data=None, json_body=False):
        body = None
        headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest", "Referer": url}
        if data is not None:
            body = (json.dumps(data) if json_body else urllib.parse.urlencode(data)).encode()
            headers["Content-Type"] = "application/json" if json_body else "application/x-www-form-urlencoded"
        request = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(request, timeout=6) as response:
            return response.read(2 * 1024 * 1024).decode("utf-8-sig")

    def lookup(self, kind, keyword, start, end):
        try:
            if kind == "야구":
                rows = self._baseball(start, end)
            elif kind == "축구":
                rows = self._football(start, end)
            else:
                rows = self._performances(keyword, start, end)
            unique = {}
            for row in rows:
                unique[(row["name"], row["date"], row["time"], row["venue"])] = row
            return list(unique.values())
        except (OSError, ValueError, ET.ParseError, TypeError, KeyError):
            return []

    def _months(self, start, end):
        return sorted({(start.year, start.month), (end.year, end.month)})

    def _baseball(self, start, end):
        result = []
        source = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
        for year, month in self._months(start, end):
            data = {"rows": []}
            for series in ["0,9,6", "3,4,5,7", "1"]:
                response = json.loads(self._request(
                    "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList",
                    {"leId": 1, "srIdList": series, "seasonId": year, "gameMonth": f"{month:02d}", "teamId": ""},
                ))
                data["rows"].extend(response.get("rows") or [])
            date = ""
            for row in data.get("rows", []):
                cells = row.get("row") or []
                for cell in cells:
                    if cell.get("Class") == "day":
                        match = re.search(r"(\d{2})\.(\d{2})", cell.get("Text") or "")
                        if match:
                            date = f"{year}-{match[1]}-{match[2]}"
                if not date or not start.isoformat() <= date <= end.isoformat():
                    continue
                times = next((cell.get("Text") or "" for cell in cells if cell.get("Class") == "time"), "")
                time = re.search(r"\d{2}:\d{2}", times)
                play = next((cell.get("Text") or "" for cell in cells if cell.get("Class") == "play"), "")
                teams = re.findall(r"<span>([^<]+)</span>", play)
                teams = [team for team in teams if team != "vs" and not team.isdigit()]
                texts = [html.unescape(re.sub(r"<[^>]+>", "", cell.get("Text") or "")).strip() for cell in cells]
                if not time or len(teams) < 2 or any("취소" in text for text in texts):
                    continue
                venue = texts[-2] if len(texts) > 1 else ""
                venue = {"잠실": "잠실야구장", "고척": "고척스카이돔"}.get(venue, venue + " 야구장")
                result.append(self._event("야구", " vs ".join([teams[0], teams[-1]]), date, time[0], venue, source))
        return result

    def _football(self, start, end):
        result = []
        source = "https://www.kleague.com/schedule.do?leagueId=1"
        for year, month in self._months(start, end):
            for league in [1, 2]:
                data = json.loads(self._request(
                    "https://www.kleague.com/getScheduleList.do",
                    {"leagueId": league, "teamId": "", "year": str(year), "month": f"{month:02d}", "ticketYn": ""},
                    json_body=True,
                ))
                for row in (data.get("data") or {}).get("scheduleList", []):
                    date = str(row.get("gameDate") or "").replace(".", "-")
                    time = str(row.get("gameTime") or "")
                    if not start.isoformat() <= date <= end.isoformat() or not re.fullmatch(r"\d{2}:\d{2}", time):
                        continue
                    if "취소" in str(row.get("gameStatus") or ""):
                        continue
                    result.append(self._event(
                        "축구", f"{row.get('homeTeamName')} vs {row.get('awayTeamName')}",
                        date, time, row.get("fieldNameFull") or row.get("fieldName") or "", source,
                    ))
        return result

    def _performances(self, keyword, start, end):
        key = self.env_value("KOPIS_API_KEY")
        if not key:
            return []
        query = urllib.parse.urlencode({
            "service": key, "stdate": start.strftime("%Y%m%d"), "eddate": end.strftime("%Y%m%d"),
            "cpage": 1, "rows": 5, "shprfnm": keyword,
        })
        root = ET.fromstring(self._request("https://www.kopis.or.kr/openApi/restful/pblprfr?" + query))
        result = []
        for item in root.findall("db")[:5]:
            identifier = item.findtext("mt20id") or ""
            if not re.fullmatch(r"PF\d+", identifier):
                continue
            details = ET.fromstring(self._request(
                "https://www.kopis.or.kr/openApi/restful/pblprfr/" + identifier
                + "?" + urllib.parse.urlencode({"service": key}),
            )).find("db")
            if details is None:
                continue
            name = details.findtext("prfnm") or ""
            venue = details.findtext("fcltynm") or ""
            guidance = details.findtext("dtguidance") or ""
            first = (details.findtext("prfpdfrom") or "").replace(".", "-")
            last = (details.findtext("prfpdto") or "").replace(".", "-")
            runtime = details.findtext("prfruntime") or ""
            duration = re.search(r"(?:(\d+)시간)?\s*(?:(\d+)분)?", runtime)
            minutes = (int(duration[1] or 0) * 60 + int(duration[2] or 0)) if duration else 0
            day = start
            while day <= end:
                date = day.isoformat()
                if first <= date <= last:
                    # Only simple weekday schedules are deterministic. Holiday/
                    # special-date notices are left for the ticket's exact session.
                    label = "월화수목금토일"[day.weekday()]
                    if not re.search(r"공휴일|변경|별도|특별", guidance):
                        for clause in re.split(r"[/;\n]", guidance):
                            if label not in clause.split("(")[0]:
                                continue
                            for time in re.findall(r"(\d{1,2}:\d{2})", clause):
                                event = self._event(
                                    "공연", name, date, time.zfill(5), venue,
                                    "https://www.kopis.or.kr/por/db/pblprfr/pblprfrView.do?mt20id=" + identifier,
                                )
                                event["region"] = item.findtext("area") or ""
                                event["duration_minutes"] = minutes or None
                                result.append(event)
                day += datetime.timedelta(days=1)
        return result

    def _event(self, kind, name, date, time, venue, source):
        return {
            "kind": kind, "name": name, "date": date, "time": time, "venue": venue,
            "source_url": source, "duration_minutes": None,
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


Model = EventSources
