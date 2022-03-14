FROM node:14.16.0-alpine as build

WORKDIR /app/frontend
COPY ./frontend/package.json ./
COPY ./frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY ./frontend/src ./src
COPY ./frontend/public ./public
COPY ./frontend/tsconfig.json ./tsconfig.json

RUN yarn build

# The second stage
# Copy React static files and start nginx
FROM nginx:stable-alpine
COPY --from=build /app/frontend/build /usr/share/nginx/html
