const { connect } = require('./db');

async function main() {
    const db = await connect();
    try {
        await db.execute(`CREATE TABLE IF NOT EXISTS together_location_consents (
            id VARCHAR(32) PRIMARY KEY,
            meeting_id VARCHAR(32) NOT NULL,
            user_id VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'inactive',
            share_duration VARCHAR(16) NOT NULL DEFAULT '60',
            expires_at DATETIME NOT NULL,
            home_enabled TINYINT(1) NOT NULL DEFAULT 1,
            stay_enabled TINYINT(1) NOT NULL DEFAULT 1,
            home_lat DOUBLE NULL,
            home_lng DOUBLE NULL,
            stay_lat DOUBLE NULL,
            stay_lng DOUBLE NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE KEY together_location_consent_participant (meeting_id, user_id),
            KEY together_location_consent_expires (expires_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`);
        await db.execute(`CREATE TABLE IF NOT EXISTS together_location_states (
            id VARCHAR(32) PRIMARY KEY,
            meeting_id VARCHAR(32) NOT NULL,
            user_id VARCHAR(32) NOT NULL,
            lat DOUBLE NOT NULL,
            lng DOUBLE NOT NULL,
            accuracy DOUBLE NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE KEY together_location_state_participant (meeting_id, user_id),
            KEY together_location_state_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`);
        await db.execute(`CREATE TABLE IF NOT EXISTS signal_meeting_message_receipts (
            id VARCHAR(64) PRIMARY KEY,
            meeting_id VARCHAR(32) NOT NULL,
            message_id VARCHAR(32) NOT NULL,
            user_id VARCHAR(32) NOT NULL,
            read_at DATETIME NOT NULL,
            UNIQUE KEY signal_meeting_receipt_user (message_id, user_id),
            KEY signal_meeting_receipt_meeting (meeting_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`);
        await db.execute("ALTER TABLE together_location_consents CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        await db.execute("ALTER TABLE together_location_states CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        await db.execute("ALTER TABLE signal_meeting_message_receipts CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        const [signalResult] = await db.execute(
            "UPDATE signals SET status = 'expired', updated_at = NOW() WHERE status = 'active' AND expires_at <= NOW()"
        );
        const [meetingResult] = await db.execute(
            "UPDATE signal_meetings SET status = 'expired', updated_at = NOW() WHERE status = 'active' AND ends_at <= NOW()"
        );
        const [matchedSignalResult] = await db.execute(
            "UPDATE signals s INNER JOIN signal_meetings m ON m.signal_id = s.id SET s.status = 'expired', s.updated_at = NOW() WHERE s.status = 'matched' AND m.status IN ('expired', 'ended')"
        );
        const [locationConsentResult] = await db.execute(
            "UPDATE together_location_consents c INNER JOIN signal_meetings m ON m.id = c.meeting_id SET c.status = 'expired', c.updated_at = NOW() WHERE c.status = 'active' AND (c.expires_at <= NOW() OR m.status IN ('expired', 'ended'))"
        );
        const [locationStateResult] = await db.execute(
            "DELETE s FROM together_location_states s LEFT JOIN together_location_consents c ON c.meeting_id = s.meeting_id AND c.user_id = s.user_id LEFT JOIN signal_meetings m ON m.id = s.meeting_id WHERE c.status <> 'active' OR c.expires_at <= NOW() OR m.status IN ('expired', 'ended')"
        );
        const [receiptResult] = await db.execute(
            "DELETE r FROM signal_meeting_message_receipts r INNER JOIN signal_meetings m ON m.id = r.meeting_id WHERE m.status IN ('expired', 'ended')"
        );
        const [messageResult] = await db.execute(
            "DELETE msg FROM signal_meeting_messages msg INNER JOIN signal_meetings m ON m.id = msg.meeting_id WHERE m.status IN ('expired', 'ended')"
        );
        console.log(JSON.stringify({
            expiredSignals: signalResult.affectedRows || 0,
            expiredMeetings: meetingResult.affectedRows || 0,
            expiredMatchedSignals: matchedSignalResult.affectedRows || 0,
            expiredLocationConsents: locationConsentResult.affectedRows || 0,
            deletedLocationStates: locationStateResult.affectedRows || 0,
            deletedMeetingReceipts: receiptResult.affectedRows || 0,
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
