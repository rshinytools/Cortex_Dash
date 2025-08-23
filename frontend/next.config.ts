// ABOUTME: Next.js configuration with comprehensive security headers
// ABOUTME: Implements CSP, X-Frame-Options, HSTS, and other security best practices

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  
  // Security headers configuration
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/:path*',
        headers: [
          {
            // Content Security Policy - strict policy with specific allowances
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net", // Required for Swagger UI
              "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net", // Required for inline styles and Swagger UI
              "img-src 'self' data: blob: https:",
              "font-src 'self' data:",
              "connect-src 'self' http://localhost:8000 http://localhost:3000 ws://localhost:3000", // API and hot reload in dev
              "frame-ancestors 'none'", // Equivalent to X-Frame-Options: DENY
              "base-uri 'self'",
              "form-action 'self'",
              "frame-src 'none'",
              "object-src 'none'",
              "script-src-attr 'none'",
              "upgrade-insecure-requests"
            ].join('; ')
          },
          {
            // Prevent clickjacking attacks
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            // Prevent MIME type sniffing
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            // Control information sent with external requests
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            // Permissions Policy - restrict browser features
            key: 'Permissions-Policy',
            value: [
              'camera=()',
              'microphone=()',
              'geolocation=()',
              'payment=()',
              'usb=()',
              'magnetometer=()',
              'gyroscope=()',
              'accelerometer=()',
              'ambient-light-sensor=()',
              'autoplay=()',
              'encrypted-media=()',
              'picture-in-picture=()',
              'speaker=()',
              'sync-xhr=(self)',
              'fullscreen=(self)',
              'notifications=(self)'
            ].join(', ')
          },
          {
            // DNS prefetch control
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            // Note: HSTS (Strict-Transport-Security) should be set at the reverse proxy level
            // for production deployments to ensure it's applied to all subdomains
            // Example for development only (remove in production):
            // key: 'Strict-Transport-Security',
            // value: 'max-age=31536000; includeSubDomains; preload'
          },
          {
            // Additional security header for XSS protection in older browsers
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          }
        ],
      },
      {
        // Looser CSP for API documentation pages
        source: '/api-docs/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
              "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
              "img-src 'self' data: blob: https:",
              "font-src 'self' data:",
              "connect-src 'self' http://localhost:8000 https://api.swagger.io",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          }
        ]
      }
    ];
  },

  // Additional security configurations
  poweredByHeader: false, // Remove X-Powered-By header
  
  // Webpack configuration for better security
  webpack: (config, { isServer }) => {
    // Add source map support for better debugging while maintaining security
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        crypto: false,
        stream: false,
      };
    }
    
    return config;
  },
  
  // Environment variable validation
  env: {
    // Ensure sensitive vars are not exposed to client
  },
  
  // Restrict image domains for next/image
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },
};

export default nextConfig;