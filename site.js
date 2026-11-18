(function(){
  const $=id=>document.getElementById(id);
  const params=new URLSearchParams(location.search);
  const escapeHtml=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const navigation=[
    ["Competitions","index.html","home"],["Stats Tracker","stats.html","stats"],
    ["Players","competition.html?view=players","players"],["Teams","competition.html?view=teams","teams"],
    ["Favorites","favorites.html","favorites"],["Advanced Lab","advanced.html","advanced"],
    ["Research","research.html","research"],["Match Centre","calendar.html","calendar"],
    ["Data Status","health.html","health"]
  ];
  const descriptions={
    stats:["Stats Tracker","The tracker layout is being prepared before statistics are added."],
    advanced:["Advanced Stats","The advanced analysis workspace will follow once the core layout is approved."],
    research:["Research Lab","A workspace for historical comparisons and research tools is being laid out."],
    weekly:["Weekly Picks & Previews","The match preview and prediction interface is being designed."],
    accuracy:["Prediction Accuracy","The accuracy dashboard layout is ready to take shape; results are not displayed in this phase."],
    calendar:["Match Centre","Fixtures, matchweeks, and match pages will live in this workspace."],
    favorites:["Favorites","A personal area for clubs and players is planned for this page."],
    news:["Football News","This page will bring football headlines into the site."],
    commentary:["Commentary Box","A workspace for analysis and editorial notes is being designed."],
    playbook:["Playbook Lab","The tactics and formation learning experience will be built here."],
    rulebook:["Football Rulebook","A clear place for football laws and explanations is being prepared."],
    health:["Data Status","Source freshness and system health will have a dedicated dashboard."],
    players:["Player Directory","Player browsing and profiles will be added after the layout pass."],
    teams:["Team Directory","Club browsing and team profiles will be added after the layout pass."],
    standings:["Standings","The competition table layout is reserved for a later data phase."],
    fixtures:["Fixtures & Results","The fixture list and matchweek controls are being laid out."],
    headtohead:["Head to Head","The club comparison experience is planned for this section."],
    records:["Records","Competition records and historical lists will be added after the layout pass."],
    profile:["Profile","This profile page is a layout shell; player and team values are hidden for now."],
    match:["Match Centre","This match page is a layout shell; scores and match statistics are hidden for now."],
    platform:["Football / Soccer","The platform is being rebuilt from the layout up."]
  };
  const tools=[
    ["📊","Core workspace","Stats Tracker","A focused place for league, season, and matchweek filters.","stats.html","stats"],
    ["🗓️","Game tracker","Match Centre","Fixture navigation and match pages for each competition.","calendar.html","calendar"],
    ["👤","Player database","Players","Player directory and profile page layouts.","competition.html?view=players","players"],
    ["🏟️","Club database","Teams","Club pages and competition team navigation.","competition.html?view=teams","teams"],
    ["📈","Deep analysis","Advanced Stats","A dedicated home for advanced football analysis.","advanced.html","advanced"],
    ["🔎","Historical tools","Research Lab","Explore the structure for season and player research.","research.html","research"],
    ["🏆","Competition history","Records","A home for competition and career record pages.","competition.html?tab=Records","records"],
    ["🎯","Match previews","Weekly Picks","A match preview and prediction workspace.","weekly.html","weekly"],
    ["🗓","Season schedule","Calendar","A season calendar and matchweek browser.","calendar.html","calendar"],
    ["✅","Model review","Accuracy","A place to review prediction performance.","accuracy.html","accuracy"],
    ["📰","League updates","Football News","A home for news and publisher links.","news.html","news"],
    ["🎙️","Editorial","Commentary Box","Create a home for stories, analysis, and notes.","commentary.html","commentary"],
    ["🧠","Tactics","Playbook Lab","Formation, roles, and tactical learning layouts.","playbook.html","playbook"],
    ["📖","Rules & learning","Rulebook","A searchable home for football laws and explanations.","rulebook.html","rulebook"],
    ["⭐","Your shortlist","Favorites","A personal space for selected clubs and players.","favorites.html","favorites"],
    ["⚙️","Reliability","Data Status","Data freshness and system health layout.","health.html","health"]
  ];
  const tabPages={"Standings":"standings","Fixtures & Results":"fixtures","Teams":"teams","Players":"players","Head to Head":"headtohead","Records":"records","Predictions":"weekly"};
  let competitions=[];
  function pageFromPath(){
    const path=location.pathname.split("/").pop()||"index.html";
    if(path==="index.html"||path==="")return "home";
    if(path==="competition.html"){
      const view=params.get("view");
      if(view)return view==="calendar"?"calendar":view;
      if(params.get("tab"))return tabPages[params.get("tab")]||"platform";
      return params.get("id")?"hub":"platform";
    }
    if(path==="entity.html")return "profile";
    if(path==="match.html")return "match";
    return path.replace(/\.html$/,"");
  }
  function selectedCompetition(){return competitions.find(item=>item.id===params.get("competition")||item.id===params.get("id"))}
  function navHtml(active){return navigation.map(item=>'<a href="./'+item[1]+'" '+(item[2]===active?'aria-current="page"':'')+'>'+escapeHtml(item[0])+'</a>').join("")}
  function common(title,description,active,content,breadcrumb){
    document.title=title+" | Football/Soccer";
    $("siteNav").innerHTML=navHtml(active);
    $("siteCrumbs").innerHTML=breadcrumb||"";
    $("siteHero").innerHTML='<div class="hero-content"><div class="eyebrow">AlexMyrusTalksSports · Football / Soccer</div><h1>'+escapeHtml(title)+'</h1><p>'+escapeHtml(description)+'</p></div>';
    $("siteContent").innerHTML=content;
  }
  function card(item,comp){
    const url=item[4].startsWith("competition.html")?"./"+item[4]+"&id="+encodeURIComponent(comp.id):"./"+item[4]+"?competition="+encodeURIComponent(comp.id);
    return '<a class="tool-card" href="'+url+'"><div class="card-top"><span class="tool-icon">'+item[0]+'</span><span class="card-arrow">↗</span></div><span class="card-tag">'+escapeHtml(item[1])+'</span><h3>'+escapeHtml(item[2])+'</h3><p>'+escapeHtml(item[3])+'</p><span class="tagline">Layout preview</span></a>';
  }
  function renderHome(){
    const groups=["All competitions",...new Set(competitions.map(item=>item.group||"Other"))];
    const hero='<div class="hero-content"><div class="eyebrow">AlexMyrusTalksSports</div><h1>Football <span>/ Soccer</span></h1><p>Choose a league, cup, or international competition. The site is starting with its page structure and visual design; statistics will be added later.</p><div class="hero-meta"><span class="meta-pill"><i class="dot"></i>Layout phase</span><span class="meta-pill">Leagues · cups · international football</span></div></div>';
    $("siteNav").innerHTML=navHtml("home");
    $("siteCrumbs").innerHTML="";
    $("siteHero").innerHTML=hero;
    $("siteContent").innerHTML='<div class="section-head"><div><h2>Explore competitions</h2><p>Open a dedicated workspace for a competition.</p></div><label class="search-wrap"><span aria-hidden="true">⌕</span><input class="search" id="competitionSearch" type="search" placeholder="Search by competition or country"></label></div><div class="filter-row" id="competitionFilters">'+groups.map((group,index)=>'<button class="filter-chip '+(index===0?'active':'')+'" type="button" data-group="'+escapeHtml(group)+'">'+escapeHtml(group)+'</button>').join("")+'</div><div id="competitionGroups"></div><div id="emptyState" class="empty-state" hidden><strong>No competitions found</strong><p>Try a different competition name or country.</p></div>';
    let activeGroup="All competitions",query="";
    const draw=()=>{
      const filtered=competitions.filter(item=>(activeGroup==="All competitions"||item.group===activeGroup)&&(!query||(item.name+" "+item.country+" "+item.kind).toLowerCase().includes(query)));
      const byGroup=new Map();
      for(const item of filtered){const key=item.group||"Other";if(!byGroup.has(key))byGroup.set(key,[]);byGroup.get(key).push(item)}
      $("competitionGroups").innerHTML=[...byGroup.entries()].map(([group,items])=>'<section><div class="section-head"><div><h2>'+escapeHtml(group)+'</h2><p>Choose a competition to continue.</p></div></div><div class="competition-grid">'+items.map(item=>'<a class="competition-card" href="./competition.html?id='+encodeURIComponent(item.id)+'"><div class="card-top"><span class="competition-code" style="color:'+escapeHtml(item.accent||"#69d5b2")+'">'+escapeHtml(item.code||"⚽")+'</span><span class="card-arrow">↗</span></div><span class="tagline">'+escapeHtml(item.country||item.kind||"Competition")+'</span><h3>'+escapeHtml(item.name)+'</h3><p>'+escapeHtml(item.kind||"Competition")+' workspace</p></a>').join("")+'</div></section>').join("");
      $("emptyState").hidden=filtered.length>0;
    };
    $("competitionFilters").addEventListener("click",event=>{const button=event.target.closest("[data-group]");if(!button)return;activeGroup=button.dataset.group;document.querySelectorAll("[data-group]").forEach(chip=>chip.classList.toggle("active",chip===button));draw()});
    $("competitionSearch").addEventListener("input",event=>{query=event.target.value.trim().toLowerCase();draw()});
    draw();
  }
  function renderHub(){
    const item=selectedCompetition();
    if(!item){renderHome();return}
    const breadcrumb='<a href="./index.html">← All competitions</a>';
    const selectedTab=params.get("tab");
    if(selectedTab){
      const view=tabPages[selectedTab]||"platform",meta=descriptions[view]||descriptions.platform;
      const content=placeholderPage(view,item);
      common(item.name+" · "+meta[0],meta[1],"",content,breadcrumb);
      return;
    }
    const toolsHtml=tools.map(entry=>card(entry,item)).join("");
    const overview='<section class="panel"><div class="section-head"><div><div class="eyebrow">'+escapeHtml(item.country||"Competition")+' · '+escapeHtml(item.kind||"Football")+'</div><h2>Competition workspace</h2><p>Browse the sections planned for this competition.</p></div><span class="badge"><i class="dot"></i>Layout preview</span></div><div class="tab-row">'+["Overview","Standings","Fixtures & Results","Teams","Players","Head to Head","Records"].map(tab=>'<a href="./competition.html?id='+encodeURIComponent(item.id)+'&tab='+encodeURIComponent(tab)+'">'+escapeHtml(tab)+'</a>').join("")+'</div><div class="empty-state"><strong>Competition sections are being laid out</strong><p>Each section will get its own page structure before any scores or statistics are brought back.</p></div></section>';
    common(item.name, (item.description||"Competition workspace").replace(/ · .*/,"")+". Explore the platform sections below. Scores and statistics are hidden while the layout is built.", "", overview+'<div class="section-head"><div><h2>Explore the platform</h2><p>Choose a tool for '+escapeHtml(item.name)+'.</p></div></div><div class="tool-grid">'+toolsHtml+'</div>',breadcrumb);
  }
  function placeholderPage(view,item){
    const title=descriptions[view]?.[0]||"Football / Soccer workspace";
    const description=descriptions[view]?.[1]||"This page is part of the layout-first rebuild.";
    const layoutKinds=["stats","advanced","research","weekly","accuracy","calendar","fixtures","standings","headtohead","records","players","teams","profile","match","health"].includes(view);
    const filters=layoutKinds?'<section class="filter-panel">'+["Competition","Season","Matchweek","View"].map(label=>'<label class="field"><span>'+escapeHtml(label)+'</span><select class="select" disabled><option>Coming soon</option></select></label>').join("")+'</section>':"";
    const skeletons='<div class="skeleton-grid">'+[0,1,2,3].map(()=>'<div class="skeleton-card" aria-hidden="true"></div>').join("")+'</div><div class="skeleton-table" aria-hidden="true">'+[0,1,2,3,4].map(()=>'<div class="skeleton-row"></div>').join("")+'</div>';
    const info='<div class="notice"><span class="notice-mark">i</span><div><strong>Layout first</strong><p>All scores, statistical values, forecasts, and data-driven tables are hidden for now. This page is a visual structure preview.</p></div></div>';
    const context=item?'<div class="hero-meta"><span class="meta-pill"><i class="dot"></i>'+escapeHtml(item.name)+'</span><a class="meta-pill" href="./competition.html?id='+encodeURIComponent(item.id)+'">Competition hub ↗</a></div>':"";
    const panel='<section class="panel"><div class="section-head"><div><h2>'+escapeHtml(title)+'</h2><p>'+escapeHtml(description)+'</p></div><span class="badge">Structure preview</span></div>'+filters+skeletons+'</section>';
    return info+context+panel;
  }
  async function boot(){
    const view=pageFromPath();
    try{const response=await fetch("./data/competitions.json");competitions=response.ok?await response.json():[]}catch{competitions=[]}
    if(view==="home"){renderHome();return}
    if(view==="hub"){renderHub();return}
    const item=selectedCompetition();
    let meta=descriptions[view]||descriptions.platform;
    if(view==="profile"){const kind=params.get("type")==="player"?"Player":"Team";meta=[kind+" Profile",kind+" profile layout preview. Profile data will be added after the page structure is settled."]}
    const active=view==="stats"?"stats":view==="players"?"players":view==="teams"?"teams":view==="favorites"?"favorites":view==="advanced"?"advanced":view==="research"?"research":view==="calendar"?"calendar":view==="health"?"health":"";
    const breadcrumb=item?'<a href="./competition.html?id='+encodeURIComponent(item.id)+'">← '+escapeHtml(item.name)+'</a> · <a href="./index.html">All competitions</a>':'<a href="./index.html">← Competitions</a>';
    common(meta[0],meta[1],active,placeholderPage(view,item),breadcrumb);
  }
  boot();
})();
