import localFont from 'next/font/local';

// 使用本地字体文件
export const geist = localFont({
  src: [
    {
      path: '../../public/fonts/geist.woff2',
      weight: '400',
      style: 'normal',
    },
  ],
  variable: '--font-geist',
});
