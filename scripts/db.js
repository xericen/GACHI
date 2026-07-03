const fs = require('node:fs');
const path = require('node:path');
const mysql = require('mysql2/promise');

function readDatabaseConfig() {
    const configPath = path.join(__dirname, '..', 'config', 'database.py');
    const source = fs.readFileSync(configPath, 'utf8');
    const match = source.match(/base\s*=\s*season\.util\.stdClass\(([\s\S]*?)\)/);
    if (!match) throw new Error('base database config not found');

    const block = match[1];
    const read = (key, fallback = '') => {
        const item = block.match(new RegExp(`${key}\\s*=\\s*["']([^"']*)["']`));
        return item ? item[1] : fallback;
    };
    const readNumber = (key, fallback) => {
        const item = block.match(new RegExp(`${key}\\s*=\\s*([0-9]+)`));
        return item ? Number(item[1]) : fallback;
    };

    return {
        host: process.env.MYSQL_HOST || read('host', '127.0.0.1'),
        port: Number(process.env.MYSQL_PORT || readNumber('port', 3306)),
        user: process.env.MYSQL_USER || read('user', 'root'),
        password: process.env.MYSQL_PASSWORD || read('password', ''),
        database: process.env.MYSQL_DATABASE || read('database', ''),
        charset: process.env.MYSQL_CHARSET || read('charset', 'utf8mb4')
    };
}

async function connect() {
    return mysql.createConnection(readDatabaseConfig());
}

function sqlDate(date = new Date()) {
    const pad = (value) => String(value).padStart(2, '0');
    return [
        date.getFullYear(),
        pad(date.getMonth() + 1),
        pad(date.getDate())
    ].join('-') + ' ' + [
        pad(date.getHours()),
        pad(date.getMinutes()),
        pad(date.getSeconds())
    ].join(':');
}

module.exports = { connect, readDatabaseConfig, sqlDate };
