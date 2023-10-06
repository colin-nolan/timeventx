export const BACKEND_API_ROOT = import.meta.env.VITE_BACKEND_API_ROOT;

if (!BACKEND_API_ROOT) {
    console.error("BACKEND_API_ROOT is not defined - distribution needs to be built with env VITE_BACKEND_API_ROOT set");
}
else {
    console.log(`BACKEND_API_ROOT is set to: ${BACKEND_API_ROOT}`);
}