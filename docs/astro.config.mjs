// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightUITweaks from 'starlight-ui-tweaks';
import starlightSidebarTopics from 'starlight-sidebar-topics';
import starlightLlmsTxt from 'starlight-llms-txt'

// https://astro.build/config
export default defineConfig({
  site: 'https://RunMercury.com',
  output: 'static',
  integrations: [
    starlight({
      title: 'Mercury',
      components: {
        // Overrides components
        Hero: './src/components/CustomHero.astro',
      },
      customCss: ['./src/styles/custom.css'],
      plugins: [
        starlightLlmsTxt(),
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
                 { label: "GitHub", href: "https://github.com/mljar/mercury" },
                 { label: "MLJAR Studio", href: "https://mljar.com" },
              ],
            },
            secondColumn: {
              title: "Resources",
              links: [
                 { label: "Documentation", href: "/docs" },
                 { label: "Examples", href: "/examples" },
                 { label: "Tutorials", href: "/tutorials" },
                 { label: "Deploy", href: "/deploy" },
              ],
            },
            thirdColumn: {
              title: "Support",
              links: [
                 { label: "Issues", href: "https://github.com/mljar/mercury/issues" },
                // { label: "Community", href: "/community" },
              ],
            },
            fourthColumn: {
              title: "Company",
              links: [
                 { label: "About", href: "https://mljar.com/about" },
                 { label: "Blog", href: "https://mljar.com/blog" },
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
                {
                  label: "Installation",
                  slug: "docs/install"
                },
                {
                  label: "Quick Start",
                  slug: "docs/quickstart"
                },
                
                { label: 'Chat', autogenerate: { directory: 'docs/chat' } },
                { label: 'Input', autogenerate: { directory: 'docs/input' } },
                { label: 'Output', autogenerate: { directory: 'docs/output' } },
                { label: 'Layout', autogenerate: { directory: 'docs/layout' } },
                { label: 'Control', autogenerate: { directory: 'docs/control' } },
                
              ]
  
          },
          {
            label: 'Examples',
            link: 'examples',
            icon: 'pencil',
            items: [
              { label: 'Examples', slug: 'examples' },
              { label: 'Chat', autogenerate: { directory: 'examples/chat' } },
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
              { label: 'Get started', slug: 'deploy' },
              { label: 'Dockerfile', slug: 'deploy/dockerfile' },
              { label: 'Cloud', slug: 'deploy/cloud' },
              
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
