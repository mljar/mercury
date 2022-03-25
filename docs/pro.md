<h1> Mercury Pro </h1>

You can extend Mercury open-source version with commercial license. Benefits of commercial license:

- additional features (for example, authentication),
- dedicated support by email,
- [white-labelling](https://mljar.com/blog/mercury-private-fork-customize/) of the Mercury web app.

After commercial license [purchase](https://mljar.com/pricing) please send us your GitHub account username. We will add you access rights to the [private repository](https://github.com/mljar/mercury-pro). The integration with Mercury OSS is straightforward, just install the Pro package (instructions are in the private repository), Mercury will detect it, and enable all features.

There is a `setup-pro.sh` script to install Mercury on VPS server for deployment with docker-compose and Pro features. You will need to set the `GITHUB_TOKEN` variable in `.env` file. Please see the [instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) on how to generate the GitHub personal access token. Please set only **repo** access ( Full control of private repositories).