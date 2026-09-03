// Cloudflare Edge Redirects Map for tanhdev.com (vesviet)
const REDIRECTS = new Map([
  // Core & Legacy Navigation
  ["/about-me", "/about/"],
  ["/about-me/", "/about/"],
  ["/contact", "/hire/"],
  ["/contact/", "/hire/"],
  ["/hire", "/hire/"],
  ["/newsletter", "/hire/"],
  ["/newsletter/", "/hire/"],
  ["/privacy", "/privacy-policy/"],
  ["/privacy/", "/privacy-policy/"],
  ["/our-services", "/"],
  ["/our-services/", "/"],
  ["/portfolio/seo-marketing", "/hire/"],
  ["/portfolio/seo-marketing/", "/hire/"],
  ["/tab-accordion", "/"],
  ["/tab-accordion/", "/"],
  ["/professional-services", "/hire/"],
  ["/professional-services/", "/hire/"],
  ["/category/development", "/categories/engineering/"],
  ["/category/development/", "/categories/engineering/"],
  ["/category/e-commerce", "/tags/e-commerce/"],
  ["/category/e-commerce/", "/tags/e-commerce/"],
  ["/wp-content/uploads/2022/12/LE-TUAN-ANH-151639.pdf", "/Le-Tuan-Anh-Resume.pdf"],

  // Post Permalinks & Consolidations
  ["/posts/golang-microservices", "/posts/go-microservices/"],
  ["/posts/golang-microservices/", "/posts/go-microservices/"],
  ["/posts/laravel-vs-golang-when-to-add-features", "/series/magento-migration-vietnam/laravel-vs-golang-when-to-add-features/"],
  ["/posts/laravel-vs-golang-when-to-add-features/", "/series/magento-migration-vietnam/laravel-vs-golang-when-to-add-features/"],
  ["/posts/is-magento-still-worth-investing-in-2026-a-practical-take-on-2.4.9-beta1-vs-2.4.8", "/series/magento-migration-vietnam/magento-still-worth-investing-2026/"],
  ["/posts/is-magento-still-worth-investing-in-2026-a-practical-take-on-2.4.9-beta1-vs-2.4.8/", "/series/magento-migration-vietnam/magento-still-worth-investing-2026/"],
  ["/posts/temporal-saga-pattern-golang-distributed-transactions", "/posts/temporal-saga-pattern-golang-distributed-transactions-guide/"],
  ["/posts/temporal-saga-pattern-golang-distributed-transactions/", "/posts/temporal-saga-pattern-golang-distributed-transactions-guide/"],
  ["/posts/magento-still-worth-investing-2026", "/series/magento-migration-vietnam/magento-still-worth-investing-2026/"],
  ["/posts/magento-still-worth-investing-2026/", "/series/magento-migration-vietnam/magento-still-worth-investing-2026/"],
  ["/posts/magento-vietnam", "/series/magento-migration-vietnam/magento-vietnam/"],
  ["/posts/magento-vietnam/", "/series/magento-migration-vietnam/magento-vietnam/"],
  ["/posts/moving-from-magento-to-microservices", "/series/magento-migration-vietnam/moving-from-magento-to-microservices/"],
  ["/posts/moving-from-magento-to-microservices/", "/series/magento-migration-vietnam/moving-from-magento-to-microservices/"],
  ["/posts/why-migrate-magento-to-microservices", "/series/magento-migration-vietnam/why-migrate-magento-to-microservices/"],
  ["/posts/why-migrate-magento-to-microservices/", "/series/magento-migration-vietnam/why-migrate-magento-to-microservices/"],
  ["/posts/exporting-magento-2-data-flat-sql-nodejs", "/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/"],
  ["/posts/exporting-magento-2-data-flat-sql-nodejs/", "/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/"],

  // Composable Commerce Legacy Slugs
  ["/series/composable-commerce-migration/executive-summary-amazon-prime-video-monolith", "/series/composable-commerce-migration/part-0-executive-summary/"],
  ["/series/composable-commerce-migration/executive-summary-amazon-prime-video-monolith/", "/series/composable-commerce-migration/part-0-executive-summary/"],

  // Cross-subdomain redirects
  ["/posts/deploying-on-cloudflare-astro-full-stack-edge-architecture-and-wordpress-behind-the-cdn", "https://learn.tanhdev.com/posts/deploying-astro-on-cloudflare-full-stack-edge-architecture/"],
  ["/posts/deploying-on-cloudflare-astro-full-stack-edge-architecture-and-wordpress-behind-the-cdn/", "https://learn.tanhdev.com/posts/deploying-astro-on-cloudflare-full-stack-edge-architecture/"],
]);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 1. Redirect www to apex domain for SEO
    if (url.hostname === 'www.tanhdev.com') {
      url.hostname = 'tanhdev.com';
      return Response.redirect(url.toString(), 301);
    }

    // 2. High-Performance Edge Redirects Lookup (O(1))
    const redirectTarget = REDIRECTS.get(url.pathname);
    if (redirectTarget) {
      const destUrl = redirectTarget.startsWith('http') ? redirectTarget : `${url.origin}${redirectTarget}`;
      return Response.redirect(destUrl, 301);
    }

    // 3. Trailing slash normalization for extension-less paths
    if (!url.pathname.endsWith('/') && !url.pathname.includes('.') && url.pathname !== '') {
      const slashPath = `${url.pathname}/`;
      const slashRedirect = REDIRECTS.get(slashPath);
      if (slashRedirect) {
        const destUrl = slashRedirect.startsWith('http') ? slashRedirect : `${url.origin}${slashRedirect}`;
        return Response.redirect(destUrl, 301);
      }
    }

    // 4. Handle OPTIONS request for CORS (Preflight)
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "Origin, Content-Type, X-Auth-Token, Authorization",
          "Access-Control-Max-Age": "300",
        }
      });
    }

    // 5. Proxy API bauxeo with Edge Caching
    if (url.pathname === '/bauxeo') {
      const day = url.searchParams.get('day') || '1';
      const apiUrl = `http://apikcnbauxeo.dulieuquantrac.com/?day=${day}`;
      
      try {
        const apiResponse = await fetch(apiUrl, {
          cf: {
            cacheTtl: 300, 
            cacheEverything: true,
          }
        });

        if (!apiResponse.ok) {
           return new Response(JSON.stringify({ error: "Failed to fetch API" }), {
               status: apiResponse.status,
               headers: { "Content-Type": "application/json" }
           });
        }

        const body = await apiResponse.text();

        return new Response(body, {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, PUT, POST, DELETE, OPTIONS",
            "Access-Control-Max-Age": "300",
            "Cache-Control": "public, max-age=300",
            "Access-Control-Allow-Headers": "Origin, Content-Type, X-Auth-Token, Authorization",
          }
        });

      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }
    }

    // 6. Branded 404 Fallback
    // When code reaches here, no static asset was matched and URL is not /bauxeo.
    // Serve Hugo's custom rendered 404.html page with HTTP 404 status.
    try {
      if (env.ASSETS) {
        const notFoundRequest = new Request(new URL('/404.html', request.url), {
          method: 'GET',
          headers: request.headers,
        });
        const notFoundResponse = await env.ASSETS.fetch(notFoundRequest);
        if (notFoundResponse && notFoundResponse.status === 200) {
          return new Response(notFoundResponse.body, {
            status: 404,
            headers: notFoundResponse.headers,
          });
        }
      }
    } catch (err) {
      // Ignore and fallback to raw 404 string
    }

    return new Response("404 Not Found", { status: 404 });
  }
};
