// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	site: 'https://synchronEnginee.github.io',
	base: '/stockblog', // TODO: Update this to match your GitHub repository name
	integrations: [mdx(), sitemap()],
});
