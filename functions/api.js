export async function onRequest(context) {
  const { request } = context;
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

  // 1. Lấy tham số 'day' (mặc định là 1)
  const day = url.searchParams.get('day') || '1';
  
  // 2. URL của API gốc
  const apiUrl = `http://apikcnbauxeo.dulieuquantrac.com/?day=${day}`;
  
  try {
    // 3. Fetch dữ liệu từ API gốc với Cloudflare Caching
    // Cloudflare tự động xử lý nén (gzip/deflate)
    const apiResponse = await fetch(apiUrl, {
      cf: {
        // Cache response trong 300s (5 phút) tại edge của Cloudflare
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

    // 4. Lấy nội dung trả về
    const body = await apiResponse.text();

    // 5. Trả về response với đầy đủ CORS headers như code PHP cũ
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
