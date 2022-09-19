module.exports = {
  settings: {
    react: {
      version: 'detect',
    },
  },
  parser: 'babel-eslint',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2018,
    sourceType: 'module',
  },
  plugins: ['react', 'prettier', 'eslint-plugin-import-helpers'],
  extends: ['react-app', 'eslint:recommended', 'plugin:react/recommended'],
  env: {
    browser: true,
    node: true,
    es6: true,
  },
  rules: {
    'prettier/prettier': 'error',
    // TODO: it might be good to add prop types and enable it eventually
    'react/prop-types': 'off',
    'no-extra-semi': 'warn',
    'no-unused-vars': ['warn', { args: 'none' }],
    'no-console': 'off',
    // TODO: https://github.com/yannickcr/eslint-plugin-react/issues/2324
    'react/display-name': 'off',
    'import-helpers/order-imports': [
      'error',
      {
        newlinesBetween: 'always',
        groups: [
          '/^react/',
          ['module', '/@lingui/', '/@sentry/', '/@testing-library/react/'],
          '/^@.*/',
          ['parent', 'sibling', 'index'],
          '/.scss$/',
        ],
      },
    ],
  },
};
