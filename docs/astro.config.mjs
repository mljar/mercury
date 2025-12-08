// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightUITweaks from 'starlight-ui-tweaks';
import starlightSidebarTopics from 'starlight-sidebar-topics';

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: 'Mercury',
      customCss: ['./src/styles/custom.css'],
      plugins: [
        starlightUITweaks({
          navbarLinks: [
            { label: 'Tutorials', href: '/tutorials/' },
            { label: 'Examples', href: '/examples/' },
            { label: 'API', href: '/api/' },
          ],
        }),
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/mljar/mercury'
        }
      ],
      sidebar: [
        {
          label: "Get Started",
          slug: "get-started-with-mercury"
        },
        {
          label: 'Widgets',
          items: [
            {
              label: 'Input Widgets',
              items: [{ label: 'Number Input', slug: 'widgets/input/number' }]
            },
            {
              label: 'Output Widgets',
              items: [{ label: 'Indicator', slug: 'widgets/output/indicator' },
              { label: 'Table', slug: 'widgets/output/table' }
            ]
            }
          ]
        }
      ]
    })
  ]
});
