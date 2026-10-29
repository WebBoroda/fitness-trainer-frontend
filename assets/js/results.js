/* Native horizontal gallery: arrow + swipe, with reduced motion support. */
(() => {
  'use strict';
  const track=document.getElementById('results-track');
  const next=document.querySelector('#results .yf-results-next');
  if(!track||!next)return;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>{next.hidden=track.scrollWidth-track.clientWidth<=3;};
  next.addEventListener('click',()=>{
    const item=track.querySelector('.yf-result-card');
    if(!item)return;
    const gap=parseFloat(getComputedStyle(track).gap)||0;
    const max=Math.max(0,track.scrollWidth-track.clientWidth);
    const left=track.scrollLeft>=max-3?0:Math.min(max,track.scrollLeft+item.getBoundingClientRect().width+gap);
    track.scrollTo({left,behavior:reduced.matches?'instant':'smooth'});
  });
  if('ResizeObserver' in window)new ResizeObserver(update).observe(track);
  else window.addEventListener('resize',update,{passive:true});
  update();
})();
