// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // Single-page application: the whole app is rendered client-side.
  ssr: false,
  devtools: { enabled: false },

  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],

  compatibilityDate: '2024-11-01',

  runtimeConfig: {
    public: {
      // Base URL of the AdRobot backend API (no trailing slash).
      // Override at build/dev time with NUXT_PUBLIC_API_BASE.
      apiBase: 'http://localhost:8000/api/v1',
      // Enable the in-browser mock when the backend is not running.
      // Set NUXT_PUBLIC_MOCK=true to enable.
      mock: false,
    },
  },

  typescript: {
    strict: true,
  },

  app: {
    head: {
      htmlAttrs: { lang: 'ru' },
      title: 'AdRobot — управление кампаниями',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Создание и настройка рекламных кампаний Keitaro' },
      ],
    },
  },
})
