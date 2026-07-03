const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_RADIUS_METERS = 600;

function loadEnvFile() {
    const candidates = [
        path.join(__dirname, '..', '.env.local'),
        path.join(__dirname, '..', '.env'),
        path.join(process.cwd(), '.env.local'),
        path.join(process.cwd(), '.env'),
        path.join(__dirname, '..', '..', '.env.local'),
        path.join(__dirname, '..', '..', '.env'),
    ];

    for (const envPath of candidates) {
        if (!fs.existsSync(envPath)) continue;
        const source = fs.readFileSync(envPath, 'utf8');
        source.split(/\r?\n/).forEach((line) => {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) return;
            const index = trimmed.indexOf('=');
            if (index < 0) return;
            const key = trimmed.slice(0, index).trim();
            let value = trimmed.slice(index + 1).trim();
            if (!key || process.env[key]) return;
            if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            process.env[key] = value;
        });
        process.env.GOOGLE_PLACES_ENV_FILE = envPath;
        return;
    }
}

loadEnvFile();

class GooglePlacesClient {
    constructor(options = {}) {
        this.apiKey = options.apiKey || process.env.GOOGLE_PLACES_API_KEY || process.env.GOOGLE_MAPS_API_KEY || process.env.GOOGLE_API_KEY || '';
        this.radius = Number(options.radius || process.env.GOOGLE_PLACES_RADIUS || DEFAULT_RADIUS_METERS);
        if (!this.apiKey) {
            throw new Error('GOOGLE_PLACES_API_KEY or GOOGLE_MAPS_API_KEY is required');
        }
    }

    async findPlace({ title, latitude, longitude, address = '' }) {
        const query = [title, address].filter(Boolean).join(' ');
        if (!query) return null;

        const params = new URLSearchParams({
            query,
            key: this.apiKey,
            language: 'ko',
            radius: String(this.radius)
        });
        if (latitude && longitude) {
            params.set('location', `${latitude},${longitude}`);
        }

        const url = `https://maps.googleapis.com/maps/api/place/textsearch/json?${params.toString()}`;
        const payload = await this.request(url);
        const candidates = payload.results || [];
        if (!candidates.length) return null;

        const scored = candidates.map((candidate) => ({
            candidate,
            score: this.scoreCandidate(candidate, { title, latitude, longitude })
        }));
        scored.sort((a, b) => b.score - a.score);
        const best = scored[0];
        if (!best || best.score < 0.35) return null;

        return {
            place_id: best.candidate.place_id,
            name: best.candidate.name || '',
            rating: best.candidate.rating || null,
            user_ratings_total: best.candidate.user_ratings_total || 0,
            score: Number(best.score.toFixed(3))
        };
    }

    async fetchPlaceDetails(placeId) {
        if (!placeId) return null;
        const params = new URLSearchParams({
            place_id: placeId,
            fields: 'place_id,name,rating,user_ratings_total,geometry',
            key: this.apiKey,
            language: 'ko'
        });
        const url = `https://maps.googleapis.com/maps/api/place/details/json?${params.toString()}`;
        const payload = await this.request(url);
        return payload.result || null;
    }

    async request(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Google Places request failed: ${response.status}`);
        }
        const payload = await response.json();
        if (payload.status && !['OK', 'ZERO_RESULTS'].includes(payload.status)) {
            throw new Error(`Google Places API error: ${payload.status} ${payload.error_message || ''}`.trim());
        }
        return payload;
    }

    scoreCandidate(candidate, source) {
        const nameScore = this.textSimilarity(candidate.name || '', source.title || '');
        const distanceScore = this.distanceScore(candidate, source);
        return (nameScore * 0.78) + (distanceScore * 0.22);
    }

    textSimilarity(a, b) {
        const left = this.normalizeText(a);
        const right = this.normalizeText(b);
        if (!left || !right) return 0;
        if (left === right) return 1;
        if (left.includes(right) || right.includes(left)) return 0.82;

        const leftTokens = new Set(left.split(' ').filter(Boolean));
        const rightTokens = new Set(right.split(' ').filter(Boolean));
        let overlap = 0;
        leftTokens.forEach((token) => {
            if (rightTokens.has(token)) overlap += 1;
        });
        return overlap / Math.max(leftTokens.size, rightTokens.size, 1);
    }

    normalizeText(value) {
        return String(value || '')
            .toLowerCase()
            .replace(/[^\p{L}\p{N}\s]/gu, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    distanceScore(candidate, source) {
        const location = candidate.geometry && candidate.geometry.location;
        if (!location || !source.latitude || !source.longitude) return 0.4;
        const distance = this.distanceMeters(
            Number(source.latitude),
            Number(source.longitude),
            Number(location.lat),
            Number(location.lng)
        );
        if (!Number.isFinite(distance)) return 0.4;
        return Math.max(0, 1 - (distance / Math.max(this.radius, 1)));
    }

    distanceMeters(lat1, lng1, lat2, lng2) {
        const earth = 6371000;
        const toRad = (value) => value * Math.PI / 180;
        const dLat = toRad(lat2 - lat1);
        const dLng = toRad(lng2 - lng1);
        const a = Math.sin(dLat / 2) ** 2
            + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
        return earth * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }
}

module.exports = GooglePlacesClient;
