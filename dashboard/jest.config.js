module.exports = {
  moduleNameMapper: {
    '^@components$': '<rootDir>/src/components',
    '^@components(.*)$': '<rootDir>/src/components$1',
    '^@images(.*)$': '<rootDir>/src/assets/images$1',
    '^@hooks$': '<rootDir>/src/hooks',
    '^@hooks(.*)$': '<rootDir>/src/hooks$1',
    '^@actions$': '<rootDir>/src/store/actions',
    '^@utils$': '<rootDir>/src/utils',
    '^@utils(.*)$': '<rootDir>/src/utils$1',
    '^@swrAPI$': '<rootDir>/src/swrAPI',
    '^@swrAPI(.*)$': '<rootDir>/src/swrAPI$1',
    '^@styles(.*)$': '<rootDir>/styles$1',
    '^@client$': '<rootDir>/client.js',
    '^@config$': '<rootDir>/config.js',
  },
};
