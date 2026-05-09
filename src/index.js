export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Xử lý OPTIONS request cho CORS (Preflight)
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

    // Nếu request vào API bauxeo
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

    // Với Workers Static Assets, nếu file tồn tại trong thư mục public, nó sẽ được phục vụ tự động.
    // Nếu code chạy đến đây, nghĩa là đường dẫn không khớp với file tĩnh nào và cũng không phải /bauxeo.
    // Mặc định trả về 404 Not Found hoặc điều hướng tới 404.html tuỳ bạn cấu hình.
    return new Response("404 Not Found", { status: 404 });
  }
};
