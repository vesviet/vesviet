---
title: "Moving from Magento to Microservices"
date: "2024-03-09 03:38:22"
categories:
  - Development
  - E-commerce
---

<!-- wp:heading -->
<h2 class="wp-block-heading">Why Microservices?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The most obvious question when considering a major move like this is, “why?” Moving away from a monolithic commerce platform is no small matter, but there are a few key reasons you might consider moving from Magento to microservices:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li><strong>Security:&nbsp;</strong>Magento—especially the self-managed, open source version—has always been a security nightmare.&nbsp;<a href="https://www.getastra.com/blog/cms/magento-security/magento-security-report-by-astra-security/" target="_blank" rel="noreferrer noopener">Sixty-two percent of Magento stores operating today</a>&nbsp;have an unaddressed security vulnerability which might leave customer or company data vulnerable to hackers.</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Technical Complexity:&nbsp;</strong>For many e-commerce stores, Magento adds&nbsp;<a href="https://paulnrogers.com/pros-and-cons-of-magento-2-a-detailed-post-adobe-view/" target="_blank" rel="noreferrer noopener">a lot of overhead</a>&nbsp;that probably isn’t necessary. For example, instead of adding attributes directly to products, developers have to&nbsp;<a href="https://devdocs.magento.com/guides/v2.4/extension-dev-guide/attributes.html" target="_blank" rel="noreferrer noopener">hook into its EAV model</a>&nbsp;to add product features. This&nbsp;<a href="https://fabric.inc/blog/magento-ecommerce-development">slows down development&nbsp;</a>and means deep, Magento-specific knowledge is required.</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Flexibility:&nbsp;</strong>As with all monolithic platforms, it can be hard to&nbsp;<a href="https://fbrnc.net/blog/2015/10/super-scaling-magento" target="_blank" rel="noreferrer noopener">granularly scale Magento</a>&nbsp;as your e-commerce application grows. Installations are typically made on a single server, and Magento doesn’t give you much room to swap out databases or add caching layers based on your needs.</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:heading -->
<h2 class="wp-block-heading">Moving from Magento to Microservices</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>While the exact process you use will vary depending on whether you’re using the open source or hosted version of Magento and how many extensions you’re using, the following is a general look at the steps you’ll need to take during your migration.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>As with any significant architecture change, I don’t recommend&nbsp;<a href="https://codingcleaner.com/the-grand-rewrite-in-the-sky/" target="_blank" rel="noreferrer noopener">a grand rewrite</a>. Instead, figure out how you’ll untangle the monolithic mess and slowly, piece by piece, move it over to microservices.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The following steps are roughly what my team did back when we made this migration a few years ago, so hopefully, this gives you a starting point for your migration today.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading" id="1-decide-where-to-start">1. Decide where to start the migration</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>One of the hardest parts about unraveling a monolith is deciding where to start. There are two approaches that teams typically take:</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p id="option-1-start-with-the-area-that-s-easiest-to-separate-and-migrate">Option 1: Start with the area that’s easiest to separate and migrate</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For example, if you have product reviews on your Magento site and they’re decoupled from the core product data, you might want to start here. Migrating product reviews to a new microservice will help you get the process started, but it probably doesn’t provide a ton of value to your business (unless product reviews happened to be limiting growth).</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p id="option-2-start-with-the-area-that-provides-the-most-business-value">Option 2: Start with the area that provides the most business value</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This was the approach my team took. We had several pieces of functionality that Magento made exceedingly hard to implement, but one big one was our in-app e-reader. We needed to allow customers to sign up, purchase a book, and then read it on our platform, but Magento wasn’t built with this use case in mind.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our engineering team started by dismantling the e-reader we hacked into Magento and moving it into a new single-page application backed by a reader microservice. At first, that service called Magento’s API to ensure the user was authenticated and had access to the book, but eventually, we migrated those services too.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Your team’s challenges will be unique. For example, if you’re trying to improve your store’s conversion rate, you might want to start with the checkout. If you’re trying to improve signup and authentication, you might start with an authentication microservice. By commencing your microservice migration with the investment that brings the most business value, you’ll build trust and give leadership a reason to continue investing in the process.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>At this stage, you should also make the&nbsp;<a href="https://resources.fabric.inc/answers/ecommerce-microservices-architecture">build vs. buy</a>&nbsp;decision. One of the advantages of microservices is that you can mix services from internal teams with those from third-party providers. This allows you to pull in a&nbsp;<a href="https://fabric.inc/blog/pim-software">PIM (product information manager)</a>&nbsp;from&nbsp;<a href="https://fabric.inc/pim?__hstc=45788219.8cdc112902254dafa759b141884fbafb.1623209324263.1623209324263.1623209324263.1&amp;__hssc=45788219.1.1623209324264&amp;__hsfp=3711082368">a company like fabric</a>&nbsp;while building your own in-house order management system if you prefer (although fabric&nbsp;<a href="https://fabric.inc/oms">offers an OMS too</a>).</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading" id="2-build-a-middle-layer">2. Build a middle layer</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>You’ll likely want to make requests to Magento from your new microservices or new user interface during your migration. In this case, an&nbsp;<a href="https://blog.netapp.com/microservices-access-data" target="_blank" rel="noreferrer noopener">API abstraction layer</a>&nbsp;is likely a good investment.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This piece—sometimes called an API gateway—acts as a router to pass all requests to either the monolith or microservices and allows you to run both in tandem while you migrate.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We did not start off using an API gateway. Instead, we made each service communicate directly with our frontend, making changes harder to manage as we moved to our microservices.</p>
<!-- /wp:paragraph -->

<!-- wp:image -->
<figure class="wp-block-image"><img src="https://fabric.inc/wp-content/uploads/hubspot/api-gateway-magento.png" alt="api-gateway-magento"/></figure>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Another element you’ll need to build as you migrate more of your functionality to microservices is&nbsp;<a href="https://resources.fabric.inc/blog/ecommerce-service-mesh">a service mesh</a>. Your service mesh handles some of the shared operational functions typically absent from microservices (e.g., logging, load balancing, routing) and helps minimize the need to duplicate functions like authentication or authorization between services.</p>
<!-- /wp:paragraph -->

<!-- wp:image -->
<figure class="wp-block-image"><img src="https://fabric.inc/wp-content/uploads/hubspot/ecommerce-microservice-architecture.png" alt="ecommerce-microservice-architecture"/></figure>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p>Whether you build your own or use&nbsp;<a href="https://fabric.inc/">fabric for your e-commerce microservices</a>, you need a solution that includes scalable networking, logging, and security models. This will ensure that latency and poor visibility don’t stop your progress towards microservices.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading" id="3-migrate-the-data-model">3. Migrate the data model</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Depending on which piece of your Magento application you decide to migrate first, getting your data out of Magento and into your new microservices can be quite a challenge.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>During our migration, getting data from some of the supporting pieces of Magento wasn’t too hard, but migrating the core product catalog proved to be a big job. We wanted to move from Magento’s fragmented EAV model to a flatter, fixed model specific to our domain.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>If your product catalog is simple, you might be able to use the&nbsp;<a href="https://docs.magento.com/user-guide/system/data-export.html" target="_blank" rel="noreferrer noopener">admin-facing Magento export feature</a>, but this option falls short if you have custom product types (like&nbsp;<a href="https://docs.magento.com/user-guide/system/data-transfer-examples.html" target="_blank" rel="noreferrer noopener">downloadable or bundled products</a>). It also doesn’t include quantity data, orders, or carts, so you’ll have to export those separately.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>You’ll likely have to write some custom PHP or SQL code to export much of your data from Magento. Because of Magento’s complex EAV table system, it’s much easier to export data if you first&nbsp;<a href="https://docs.magento.com/user-guide/catalog/catalog-flat.html" target="_blank" rel="noreferrer noopener">switch to their flat catalog</a>. After that, your product catalog will be cached into a single flat table which is easier to export and query against.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Next, you have to export data for orders, customers, carts, etc. Doing so will be a tedious process as each requires its own SQL query. For example, this query will get your orders with their payment and shipment IDs:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>SELECT sales_order.entity_id AS "Order ID",
    sales_order_payment.entity_id AS "Payment ID",
    sales_shipment.entity_id AS "Shipment ID"
FROM sales_order
     LEFT JOIN sales_order_payment ON (sales_order.entity_id = sales_order_payment.parent_id)
     LEFT JOIN sales_shipment ON (sales_order.entity_id = sales_shipment.entity_id)
     # Note: you can add any filters as WHERE queries here
ORDER BY sales_order.created_at
</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>Now you can export each of these query results to a .csv file and import them into your new microservice. This import process will vary depending on the language of your new service and shape of your new database, but it could be a simple Node script.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This example uses the popular&nbsp;<a href="https://www.npmjs.com/package/csv-parse" target="_blank" rel="noreferrer noopener"><code>csv-parse</code></a>&nbsp;package:</p>
<!-- /wp:paragraph -->

<!-- wp:code -->
<pre class="wp-block-code"><code>const db = require('./database');
const fs = require('fs');
const parse = require('csv-parse');
 
const parser = parse({columns: true}, function (err, orders) {
    orders.forEach(function (order) {
        // You can transform your data or save it here
        db.save(order);
    });
});
 
fs.createReadStream(__dirname+'/orders.csv').pipe(parser);
</code></pre>
<!-- /wp:code -->

<!-- wp:paragraph -->
<p>If you want to run both Magento and your new service in tandem, you’ll need to set up a data pipeline so that records are piped to your new microservice whenever they are added. MySQL&nbsp;<a href="https://stackoverflow.com/questions/20363805/mysql-creating-trigger-on-view-error-1347" target="_blank" rel="noreferrer noopener">doesn’t support triggers on views</a>, so you’ll have to set up a service to check for updates and pipe them over to your new database.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading" id="4-test-replace-repeat">4. Test, replace, repeat</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>As we migrated pieces of our infrastructure from Magento to microservices, we tested the changes and kept a close eye on the logs. If we saw anything that looked out of place, we’d roll back or quickly push a fix to the broken service. We repeated this process for each major piece of our e-commerce store until all the microservices were rolled out.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our application was relatively small, but it still took our team almost a year to complete the migration. During the process, we sped up and simplified our application significantly, and ultimately helped the business learn more and iterate on our offerings faster.</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading" id="conclusion">Conclusion</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>As you’ve seen, migrating to microservices from Magento is no small task. It could take months or years, but if you can start small with the pieces that provide the most business value, it’s a worthwhile investment.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>On the other hand, if you’d prefer not to make this migration on your own,&nbsp;<a href="http://fabric.inc/">let our team know</a>. fabric offers a scalable microservice-based solution for e-commerce stores that need to scale up. We can help you carry out a migration from your existing Magento store and ensure that your business continues to grow along the way.</p>
<!-- /wp:paragraph -->