# Next.js frontend — works with either Railway layout:
#   • Root Directory = frontend   (build context = frontend/)
#   • Root Directory = repo root  (build context = ., Dockerfile path = frontend/Dockerfile)

FROM node:22-alpine AS src
WORKDIR /src
COPY . .
RUN set -eux; \
    if [ -f package.json ]; then \
      APP=.; \
    elif [ -f frontend/package.json ]; then \
      APP=frontend; \
    else \
      echo "ERROR: package.json not found (expected at ./ or ./frontend/)" >&2; \
      ls -la . >&2; \
      exit 1; \
    fi; \
    mkdir -p /build && cp -a "$APP"/. /build/

FROM node:22-alpine
WORKDIR /app

COPY --from=src /build/package.json /build/package-lock.json ./
RUN npm ci

COPY --from=src /build/ .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# Railway injects PORT at runtime; Next.js reads PORT + HOSTNAME from the environment.
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

EXPOSE 3000

CMD ["node", "node_modules/next/dist/bin/next", "start"]
