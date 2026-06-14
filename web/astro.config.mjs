// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import sitemap from '@astrojs/sitemap';

// When a custom domain is connected later, set SITE to it and BASE to '/'.
const SITE = process.env.SITE_URL || 'https://contact993.github.io';
const BASE = process.env.BASE_PATH || '/corepeak';

const softwareJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Corepeak',
  applicationCategory: 'ScienceApplication',
  operatingSystem: 'macOS, Windows',
  description:
    'Free, cross-platform XPS (X-ray photoelectron spectroscopy) peak-fitting app with a built-in fit auditor and a citation-backed reference database. The modern replacement for XPSPEAK 4.1.',
  url: SITE + BASE + '/',
  downloadUrl: 'https://github.com/contact993/xpsfit/releases',
  softwareVersion: '0.1.0',
  license: 'https://www.gnu.org/licenses/gpl-3.0.html',
  offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  author: { '@type': 'Person', name: 'Taehee Kim' },
};

export default defineConfig({
  site: SITE,
  base: BASE,
  integrations: [
    sitemap(),
    starlight({
      title: 'Corepeak',
      tagline: 'Free XPS peak fitting for Mac & Windows — with a built-in fit auditor',
      description:
        'Free, cross-platform XPS peak-fitting software with a fit auditor and a citation-backed reference database. The modern XPSPEAK 4.1 replacement.',
      social: { github: 'https://github.com/contact993/xpsfit' },
      customCss: ['./src/styles/custom.css'],
      defaultLocale: 'root',
      locales: {
        root: { label: 'English', lang: 'en' },
        ko: { label: '한국어', lang: 'ko' },
      },
      components: {
        Footer: './src/components/Footer.astro',
      },
      head: [
        {
          tag: 'script',
          attrs: { type: 'application/ld+json' },
          content: JSON.stringify(softwareJsonLd),
        },
        // Social / Open Graph image (helps link previews drive traffic)
        { tag: 'meta', attrs: { property: 'og:image', content: SITE + BASE + '/screenshot.png' } },
        { tag: 'meta', attrs: { property: 'og:type', content: 'website' } },
        { tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' } },
        { tag: 'meta', attrs: { name: 'twitter:image', content: SITE + BASE + '/screenshot.png' } },
        { tag: 'meta', attrs: { name: 'keywords', content: 'XPS, X-ray photoelectron spectroscopy, peak fitting, curve fitting, XPSPEAK alternative, CasaXPS alternative, free XPS software, surface analysis, Mac' } },
      ],
      sidebar: [
        { label: 'Download', translations: { ko: '다운로드' }, link: '/download/' },
        { label: 'Features', translations: { ko: '기능' }, link: '/features/' },
        { label: 'Compare', translations: { ko: '비교' }, link: '/compare/' },
        {
          label: 'Guides',
          translations: { ko: '가이드' },
          items: [
            { label: 'Shirley vs Tougaard background', link: '/guides/shirley-vs-tougaard/' },
            { label: 'Spin-orbit doublet fitting', link: '/guides/doublet-fitting/' },
            { label: 'The fit audit (BIC / leave-one-out)', link: '/guides/fit-audit/' },
          ],
        },
        { label: 'Cite', translations: { ko: '인용' }, link: '/cite/' },
        { label: 'Feedback', translations: { ko: '피드백·기능요청' }, link: '/feedback/' },
        { label: 'Contribute a reference', translations: { ko: '레퍼런스 제보' }, link: '/contribute/' },
      ],
    }),
  ],
});
