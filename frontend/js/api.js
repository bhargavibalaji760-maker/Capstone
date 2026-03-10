const API_BASE = window.location.port !== '3000' && window.location.hostname === 'localhost'
     ? "http://localhost:3000/api/v1"
     : "/api/v1";

const api = {
     // Helper: get auth headers
     getHeaders() {
          const token = localStorage.getItem("access_token")?.trim();
          const headers = {
               "Content-Type": "application/json",
               ...(token ? { "Authorization": `Bearer ${token}` } : {})
          };
          return headers;
     },

     async request(path, options = {}) {
          const url = API_BASE + path;
          const token = localStorage.getItem("access_token")?.trim();
          
          // Debug token presence
          if (!token && !url.includes("/auth/")) {
               console.warn(`[API] No token available for protected route: ${path}`);
          }

          // Don't set Content-Type for FormData — let the browser set the multipart boundary
          const isFormData = options.body instanceof FormData;
          const headers = {
               ...(token ? { "Authorization": `Bearer ${token}` } : {}),
               ...(isFormData ? {} : { "Content-Type": "application/json" }),
               ...(options.headers || {})
          };

          if (token && !url.includes("/auth/")) {
               console.log(`[API] ${options.method || 'GET'} ${path} | Auth: Bearer ${token.substring(0, 10)}...`);
          }

          try {
               const res = await fetch(url, { ...options, headers });

               // Redirect to login if unauthorized
                if (res.status === 401 && !url.includes("/auth/")) {
                    console.error(`[API] 401 Unauthorized on ${path}. Key session compromised.`);
                    this.gracefulRedirect("/login");
                    return null;
                }

               if (!res.ok) throw await res.json();

               return await res.json();
          } catch (err) {
               throw err;
          }
     },

     get(path) {
          return this.request(path, { method: "GET" });
     },

     post(path, body) {
          return this.request(path, {
               method: "POST",
               body: JSON.stringify(body)
          });
     },

     put(path, body) {
          return this.request(path, {
               method: "PUT",
               body: JSON.stringify(body)
          });
     },

     delete(path) {
          return this.request(path, { method: "DELETE" });
     },

     async logout() {
          try {
               await this.post("/auth/logout");
          } catch (e) {
               console.warn("Logout endpoint failed:", e);
          }
          this.gracefulRedirect("/login");
     },

     checkAuth() {
          const token = localStorage.getItem("access_token");
          const path = window.location.pathname.replace(/\/$/, ""); // Normalize trailing slash
          const isLoginPage = ["/login", "/signup", "/login.html", "/signup.html", "", "/index.html"].includes(path);

          if (!token && !isLoginPage) {
               console.log("No token found, redirecting to login...");
               this.gracefulRedirect("/login");
               return false;
          }
          
          if (token && isLoginPage) {
               console.log("Token found on login page, redirecting home...");
               this.gracefulRedirect("/dashboard");
               return false;
          }
          return true;
     },

     gracefulRedirect(target) {
          if (target === "/login") {
               localStorage.removeItem("access_token");
               // Optionally clear all if you want a complete reset
               // localStorage.clear();
          }
          
          document.body.classList.remove("loaded");
          setTimeout(() => {
               // Use replace instead of href to prevent back-button recursion
               window.location.replace(target);
          }, 300);
     },

     verifySession() {
          // 1. Initial Auth Check
          if (!this.checkAuth()) return;

          // 2. Smooth Reveal Logic
          const reveal = () => {
               const loader = document.getElementById("pageLoader") || document.querySelector(".page-loader");
               
               // Small timeout to ensure initial layout is stable
               setTimeout(() => {
                    if (loader) {
                         loader.style.opacity = "0";
                         setTimeout(() => {
                              loader.remove();
                              document.body.classList.add("loaded");
                         }, 400);
                    } else {
                         document.body.classList.add("loaded");
                    }
               }, 400);
          };

          if (document.readyState === "complete") {
               reveal();
          } else {
               window.addEventListener("load", reveal);
          }
     }
};

// Global Auth Check for BFCache (Back/Forward Cache)
window.addEventListener("pageshow", (event) => {
     // If the page is loaded from cache (e.g. back button)
     if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
          api.checkAuth();
     }
});

// Auto-run auth check on script load
if (typeof window !== 'undefined') {
     api.checkAuth();
}
