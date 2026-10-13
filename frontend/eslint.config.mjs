import js from '@eslint/js';
import tseslint from 'typescript-eslint';
export default tseslint.config(
  {ignores:['dist/**','node_modules/**','test-results/**','playwright-report/**']},
  {files:['src/**/*.{ts,tsx}'], extends:[js.configs.recommended,...tseslint.configs.recommended],
    rules:{'@typescript-eslint/no-explicit-any':'off','@typescript-eslint/no-unused-vars':['warn',{argsIgnorePattern:'^_'}]}},
);
