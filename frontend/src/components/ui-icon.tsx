export type IconName = "check-circle"|"heart"|"bookmark"|"headphones"|"pen"|"plus"|"trash"|"list-plus"|"arrow-up"|"arrow-down"|"arrow-right"|"arrow-up-right"|"chevron-right"|"search";
const paths:Record<IconName,string> = {
"check-circle":"M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0M7.5 12l3 3 6-6",
heart:"M20.8 4.6a5.5 5.5 0 0 0-7.8 0l-1 1-1-1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z",
bookmark:"M6 3h12v18l-6-4-6 4Z",headphones:"M3 14v-3a9 9 0 0 1 18 0v3M3 13h4v7H5a2 2 0 0 1-2-2Zm18 0h-4v7h2a2 2 0 0 0 2-2Z",
pen:"m14 5 5 5M4 20l5-1 12-12-5-5L4 14Z",plus:"M12 5v14M5 12h14",trash:"M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 10v7m4-7v7","list-plus":"M4 6h12M4 12h12M4 18h8M18 15v6m-3-3h6",
"arrow-up":"m6 10 6-6 6 6M12 4v16","arrow-down":"m6 14 6 6 6-6M12 4v16","arrow-right":"M4 12h16m-6-6 6 6-6 6","arrow-up-right":"M6 18 18 6M7 6h11v11","chevron-right":"m9 6 6 6-6 6",search:"M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0m-2 5 6 6"};
export function UiIcon({name,size=20}:{name:IconName;size?:number}) { return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]}/></svg>; }
