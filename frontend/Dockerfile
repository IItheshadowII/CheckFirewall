# Build Stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
# Ensure devDependencies (like vite) are installed during the build
ENV NPM_CONFIG_PRODUCTION=false
RUN npm ci --prefer-offline --no-audit
COPY . .
RUN npm run build

# Production Stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Inject runtime env (VITE_API_URL, VITE_API_KEY) into /usr/share/nginx/html/env.js
# at container startup. This avoids hardcoding secrets into the bundle.
COPY docker-entrypoint.d/99-runtime-env.sh /docker-entrypoint.d/99-runtime-env.sh
RUN chmod +x /docker-entrypoint.d/99-runtime-env.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
