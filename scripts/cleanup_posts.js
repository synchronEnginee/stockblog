import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BLOG_DIR = path.join(__dirname, '../src/content/blog');
const MAX_AGE_DAYS = 180; // 6 months

function deleteOldPosts() {
    if (!fs.existsSync(BLOG_DIR)) {
        console.log(`Directory not found: ${BLOG_DIR}`);
        return;
    }

    const files = fs.readdirSync(BLOG_DIR);
    const now = new Date();

    files.forEach(file => {
        // Expected format: YYYY-MM-DD-stock-report.md
        const match = file.match(/^(\d{4}-\d{2}-\d{2})-.*\.md$/);

        if (match) {
            const dateStr = match[1];
            const fileDate = new Date(dateStr);

            // Calculate difference in days
            const diffTime = Math.abs(now - fileDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays > MAX_AGE_DAYS) {
                console.log(`Deleting old post: ${file} (${diffDays} days old)`);
                fs.unlinkSync(path.join(BLOG_DIR, file));
            } else {
                // console.log(`Keeping post: ${file} (${diffDays} days old)`);
            }
        }
    });
}

deleteOldPosts();
