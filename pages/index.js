- import Landing from './landing';
 import Link from 'next/link';
@@ -2,1 +2,1 @@
- export default function Home() {
 export default function HomePage() {
@@ -3,1 +3,5 @@
-   return <Landing />;
   return (
     <div>
       <Link href="/landing">Go to Landing Page</Link>
     </div>
   );