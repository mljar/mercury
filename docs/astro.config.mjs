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
            { label: 'Documentation', href: '/docs/' },
            { label: 'Examples', href: '/examples/' },
            { label: 'Tutorials', href: '/tutorials/' },
            { label: 'Deploy', href: '/deploy/' },
          ],
          footer: {
            copyright: "MLJAR Sp. z o.o. - all rights reserved.",
            firstColumn: {
              title: "Product",
              links: [
                // { label: "Features", href: "/features" },
                // { label: "Pricing", href: "/pricing" },
              ],
            },
            secondColumn: {
              title: "Resources",
              links: [
                // { label: "Documentation", href: "/docs" },
                // { label: "Guides", href: "/guides" },
              ],
            },
            thirdColumn: {
              title: "Support",
              links: [
                // { label: "Help Center", href: "/help" },
                // { label: "Community", href: "/community" },
              ],
            },
            fourthColumn: {
              title: "Company",
              links: [
                // { label: "About", href: "/about" },
                // { label: "Blog", href: "/blog" },
              ],
            },
          },
        }),
        starlightSidebarTopics([
          {
            label: 'Documentation',
            link: "docs",
            icon: 'document',
            items:

              [
                {
                  label: "Documentation",
                  slug: "docs"
                },
                { label: 'Input Widgets', autogenerate: { directory: 'docs/widgets/input' } },
                { label: 'Output Widgets', autogenerate: { directory: 'docs/widgets/output' } },
              ]
            ,
          },
          {
            label: 'Examples',
            link: 'examples',
            icon: 'pencil',
            items: [
              { label: 'Examples', slug: 'examples' }
            ],
          },
          {
            label: 'Tutorials',
            link: 'tutorials',
            icon: 'star',
            items: [
              { label: 'Get started tut', slug: 'tutorials' }
            ],
          },
          {
            label: 'Deploy',
            link: 'deploy',
            icon: 'rocket',
            items: [
              { label: 'Get started tut', slug: 'deploy' }
            ],
          },
        ]),
      ],
      // components: {
      //   Footer: './src/components/Footer.astro',
      // },
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/mljar/mercury'
        }
      ],
      // sidebar: [
      //   {
      //     label: "Get Started",
      //     slug: "get-started-with-mercury"
      //   },
      //   {
      //     label: 'Widgets',
      //     items: [
      //       {
      //         label: 'Input Widgets',
      //         items: [{ label: 'Number Input', slug: 'widgets/input/number' }]
      //       },
      //       {
      //         label: 'Output Widgets',
      //         items: [{ label: 'Indicator', slug: 'widgets/output/indicator' },
      //         { label: 'Table', slug: 'widgets/output/table' }
      //       ]
      //       }
      //     ]
      //   }
      // ]
    })
  ]
});
