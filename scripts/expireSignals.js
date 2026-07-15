const { connect } = require('./db');

async function main() {
    const db = await connect();
    try {
        const [signalResult] = await db.execute(
            "UPDATE signals SET status = 'expired', updated_at = NOW() WHERE status = 'active' AND expires_at <= NOW()"
        );
        const [meetingResult] = await db.execute(
            "UPDATE signal_meetings SET status = 'expired', updated_at = NOW() WHERE status = 'active' AND ends_at <= NOW()"
        );
        const [matchedSignalResult] = await db.execute(
            "UPDATE signals s INNER JOIN signal_meetings m ON m.signal_id = s.id SET s.status = 'expired', s.updated_at = NOW() WHERE s.status = 'matched' AND m.status IN ('expired', 'ended')"
        );
        const [messageResult] = await db.execute(
            "DELETE msg FROM signal_meeting_messages msg INNER JOIN signal_meetings m ON m.id = msg.meeting_id WHERE m.status IN ('expired', 'ended')"
        );
        console.log(JSON.stringify({
            expiredSignals: signalResult.affectedRows || 0,
            expiredMeetings: meetingResult.affectedRows || 0,
            expiredMatchedSignals: matchedSignalResult.affectedRows || 0,
            deletedMeetingMessages: messageResult.affectedRows || 0,
            checkedAt: new Date().toISOString()
        }));
    } finally {
        await db.end();
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
