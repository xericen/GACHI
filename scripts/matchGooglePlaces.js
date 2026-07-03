const GooglePlacesClient = require('../services/googlePlacesClient');
const { connect } = require('./db');

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
    const limit = Math.max(1, Math.min(Number(process.env.LIMIT || 200), 1000));
    const delay = Number(process.env.GOOGLE_PLACES_DELAY_MS || 120);
    const client = new GooglePlacesClient();
    const db = await connect();

    try {
        const [places] = await db.execute(
            `SELECT id, name, address, latitude, longitude
             FROM \`place\`
             WHERE (google_place_id IS NULL OR google_place_id = '')
               AND is_hidden = 0
             LIMIT ${limit}`
        );

        for (const place of places) {
            try {
                const match = await client.findPlace({
                    title: place.name,
                    address: place.address,
                    latitude: place.latitude,
                    longitude: place.longitude
                });
                if (match && match.place_id) {
                    await db.execute(
                        `UPDATE \`place\`
                         SET google_place_id = ?, google_rating = ?, google_user_ratings_total = ?, google_rating_cached_at = NOW()
                         WHERE id = ?`,
                        [match.place_id, match.rating, match.user_ratings_total || 0, place.id]
                    );
                    console.log(`matched ${place.name} -> ${match.place_id} (${match.score})`);
                } else {
                    console.log(`no match ${place.name}`);
                }
            } catch (error) {
                console.error(`failed ${place.name}: ${error.message}`);
            }
            if (delay > 0) await sleep(delay);
        }
    } finally {
        await db.end();
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
