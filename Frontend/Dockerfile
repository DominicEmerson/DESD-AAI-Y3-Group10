FROM nginx:alpine

# Set the working directory inside the container
WORKDIR /app

# import nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the port frontend runs on
EXPOSE 8080

# Start nginx directly
CMD ["nginx", "-g", "daemon off;"]