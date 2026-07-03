const { connect } = require('./db');
const crypto = require('node:crypto');

async function ensureColumn(db, table, column, ddl) {
    const [rows] = await db.query(`SHOW COLUMNS FROM \`${table}\` LIKE ${db.escape(column)}`);
    if (rows.length > 0) return;
    await db.execute(`ALTER TABLE \`${table}\` ADD COLUMN ${ddl}`);
}

async function markDummyRows(db) {
    await db.execute(
        `UPDATE \`place\`
         SET is_hidden = 1,
             description = CASE
                 WHEN description LIKE '[더미]%' THEN description
                 ELSE CONCAT('[더미] ', description)
             END,
             updated = NOW()
         WHERE tourapi_id LIKE 'TOUR-%' OR tourapi_id LIKE 'DUMMY-%'`
    );
    await db.execute(
        `UPDATE course
         SET is_featured = 0,
             is_hidden = 1,
             tags = '[\"더미\"]',
             updated = NOW()
         WHERE title LIKE '검증용 인기 코스%'`
    );
}

async function main() {
    const db = await connect();
    try {
        await db.execute(`CREATE TABLE IF NOT EXISTS \`course_places\` (
            \`id\` VARCHAR(32) NOT NULL PRIMARY KEY,
            \`course_id\` VARCHAR(32) NOT NULL,
            \`place_id\` VARCHAR(32) NOT NULL,
            \`order_index\` INT NOT NULL DEFAULT 1,
            \`created\` DATETIME NOT NULL,
            UNIQUE KEY \`course_places_course_place\` (\`course_id\`, \`place_id\`),
            KEY \`course_places_course_id\` (\`course_id\`),
            KEY \`course_places_place_id\` (\`place_id\`)
        ) DEFAULT CHARSET=utf8mb4`);

        await db.execute(`CREATE TABLE IF NOT EXISTS \`course_likes\` (
            \`id\` VARCHAR(32) NOT NULL PRIMARY KEY,
            \`course_id\` VARCHAR(32) NOT NULL,
            \`user_id\` VARCHAR(32) NULL,
            \`created\` DATETIME NOT NULL,
            UNIQUE KEY \`course_likes_course_user\` (\`course_id\`, \`user_id\`),
            KEY \`course_likes_course_id\` (\`course_id\`),
            KEY \`course_likes_user_id\` (\`user_id\`)
        ) DEFAULT CHARSET=utf8mb4`);

        await ensureColumn(db, 'course', 'region', "`region` VARCHAR(100) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'course', 'cover_image', "`cover_image` VARCHAR(500) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'course', 'duration_type', "`duration_type` VARCHAR(16) NOT NULL DEFAULT 'hours'");
        await ensureColumn(db, 'course', 'duration_value', "`duration_value` VARCHAR(50) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'course', 'rating', '`rating` DOUBLE NULL');
        await ensureColumn(db, 'course', 'is_featured', '`is_featured` TINYINT(1) NOT NULL DEFAULT 0');

        await ensureColumn(db, 'place', 'google_place_id', "`google_place_id` VARCHAR(128) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'google_rating', '`google_rating` DOUBLE NULL');
        await ensureColumn(db, 'place', 'google_user_ratings_total', '`google_user_ratings_total` INT NOT NULL DEFAULT 0');
        await ensureColumn(db, 'place', 'google_rating_cached_at', "`google_rating_cached_at` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'first_image2', "`first_image2` VARCHAR(500) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'zipcode', "`zipcode` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'cpyrht_div_cd', "`cpyrht_div_cd` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'ldong_regn_cd', "`ldong_regn_cd` VARCHAR(10) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'ldong_signgu_cd', "`ldong_signgu_cd` VARCHAR(10) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'lcls_systm1', "`lcls_systm1` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'lcls_systm2', "`lcls_systm2` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'lcls_systm3', "`lcls_systm3` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'tourapi_created_time', "`tourapi_created_time` VARCHAR(20) NOT NULL DEFAULT ''");
        await ensureColumn(db, 'place', 'tourapi_modified_time', "`tourapi_modified_time` VARCHAR(20) NOT NULL DEFAULT ''");

        const [courses] = await db.execute('SELECT id, place_ids FROM course');
        for (const course of courses) {
            const [existing] = await db.execute('SELECT COUNT(*) AS count FROM course_places WHERE course_id = ?', [course.id]);
            if (existing[0].count > 0) continue;
            let placeIds = [];
            try {
                placeIds = JSON.parse(course.place_ids || '[]');
            } catch (e) {
                placeIds = [];
            }
            if (!Array.isArray(placeIds)) continue;
            for (let index = 0; index < placeIds.length; index += 1) {
                if (!placeIds[index]) continue;
                await db.execute(
                    `INSERT IGNORE INTO course_places (id, course_id, place_id, order_index, created)
                     VALUES (?, ?, ?, ?, NOW())`,
                    [crypto.randomBytes(16).toString('hex'), course.id, placeIds[index], index + 1]
                );
            }
        }

        const [featured] = await db.execute('SELECT COUNT(*) AS count FROM course WHERE is_featured = 1');
        if (featured[0].count === 0) {
            await db.execute(
                `UPDATE course
                 SET is_featured = 1, updated = NOW()
                 WHERE is_hidden = 0
                 ORDER BY display_order ASC, created ASC
                 LIMIT 4`
            );
        }

        await markDummyRows(db);
    } finally {
        await db.end();
    }
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});
