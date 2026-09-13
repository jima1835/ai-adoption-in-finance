import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'

// Flat config for the React site in src/ (`npm run lint`). Prettier owns
// formatting (`npm run format:check`); ESLint here is for correctness only.
export default [
  { ignores: ['docs/**', 'node_modules/**'] },
  js.configs.recommended,
  react.configs.flat.recommended,
  react.configs.flat['jsx-runtime'],
  reactHooks.configs.flat.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
    },
    settings: { react: { version: 'detect' } },
    rules: {
      // No PropTypes in this codebase; props are documented at each component.
      'react/prop-types': 'off',
    },
  },
]
