const { connect } = require('./db');

async function main() {
    const db = await connect();
    try {
        const [result] = await db.execute(
            "UPDATE signals SET status = 'expired', updated_at = NOW() WHERE status = 'active' AND expires_at <= NOW()"
        );
        console.log(JSON.stringify({
            expired: result.affectedRows || 0,
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
