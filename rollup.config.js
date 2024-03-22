import babel from 'rollup-plugin-babel'

export default {
  input: 'src/aac-repair.js',
  output: {
    file: 'bin/aac-repair.js',
    format: 'cjs',
    banner: '#!/usr/bin/env node'
  },
  plugins: [
    babel({
      exclude: 'node_modules/**'
    })
  ],
  external: [
    'cors',
    'express',
    'express-fileupload',
    'fs-extra',
    'out-url'
  ]
}