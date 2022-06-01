<h1> Export notebook to PDF or HTML </h1>

Notebooks that are executed in the `Mercury` can be exported to standalone HTML or PDf file. Please click the `Download` button in the sidebar and select the desired format.

<img 
    style="border: 1px solid #e1e4e5"
    alt="Download executed notebook as PDF"
    src="https://user-images.githubusercontent.com/6959032/169780484-67cd4ffc-f41a-4bcb-8bf3-cc0c3d1119c2.gif" width="100%" />


## Export to PDF

For Heroku deployments you need to add a buildpack `https://github.com/jontewks/puppeteer-heroku-buildpack` to enable PDF export feature. For `docker-compose` deployments everything is aleary included.