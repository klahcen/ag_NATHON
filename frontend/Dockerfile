# Next.js frontend — build context must be the frontend/ directory (Railway root directory).
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked at build time for client-side fetch (set in Railway → frontend → Variables).
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["sh", "-c", "exec npm run start -- -p ${PORT:-3000}"]
