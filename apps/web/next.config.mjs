const nextConfig = {
  output: "standalone",
  transpilePackages: [
    "@oldpages/api-client",
    "@oldpages/config",
    "@oldpages/design-tokens",
    "@oldpages/shared-types",
    "@oldpages/validation",
  ],
};

export default nextConfig;
