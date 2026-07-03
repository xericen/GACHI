const GooglePlacesClient = require('../services/googlePlacesClient');
const { connect, sqlDate } = require('./db');

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function updateCourseRatings(db) {
    const [rows] = await db.execute(
        `SELECT cp.course_id, AVG(p.google_rating) AS rating
         FROM course_places cp
         JOIN \`place\` p ON p.id = cp.place_id
         WHERE p.google_rating IS NOT NULL
         GROUP BY cp.course_id`
    );

    for (const row of rows) {
        await db.execute(
            `UPDATE \`course\` SET rating = ?, updated = NOW() WHERE id = ?`,
            [Number(row.rating).toFixed(1), row.course_id]
        );
    }
}

async function main() {
    const limit = Math.max(1, Math.min(Number(process.env.LIMIT || 200), 1000));
    const delay = Number(process.env.GOOGLE_PLACES_DELAY_MS || 120);
    const cacheDays = Number(process.env.GOOGLE_RATING_CACHE_DAYS || 7);
    const cutoff = new Date(Date.now() - cacheDays * 24 * 60 * 60 * 1000);
    const client = new GooglePlacesClient();
    const db = await connect();

    try {
        const [places] = await db.execute(
            `SELECT id, name, google_place_id
             FROM \`place\`
             WHERE google_place_id <> ''
               AND (google_rating_cached_at IS NULL OR google_rating_cached_at = '' OR google_rating_cached_at < ?)
             LIMIT ${limit}`,
            [sqlDate(cutoff)]
        );

        for (const place of places) {
            try {
                const details = await client.fetchPlaceDetails(place.google_place_id);
                if (details) {
                    await db.execute(
                        `UPDATE \`place\`
                         SET google_rating = ?, google_user_ratings_total = ?, google_rating_cached_at = NOW()
                         WHERE id = ?`,
                        [details.rating || null, details.user_ratings_total || 0, place.id]
                    );
                    console.log(`rating ${place.name}: ${details.rating || '-'}`);
                }
            } catch (error) {
                console.error(`failed ${place.name}: ${error.message}`);
            }
            if (delay > 0) await sleep(delay);
        }

        await updateCourseRatings(db);
    } finally {
        await db.end();
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
