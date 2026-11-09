const COMPETITIONS = [
  {id:"premier-league",name:"Premier League",country:"England",kind:"League",group:"Leagues",season:"2026/27",code:"PL",accent:"#e56bff",description:"English top flight · clubs, standings, match calendar and season history."},
  {id:"ligue-1",name:"Ligue 1",country:"France",kind:"League",group:"Leagues",season:"2026/27",code:"L1",accent:"#67b8ff",description:"French top flight · clubs, standings, match calendar and season history."},
  {id:"la-liga",name:"La Liga",country:"Spain",kind:"League",group:"Leagues",season:"2026/27",code:"LL",accent:"#ff786c",description:"Spanish top flight · clubs, standings, match calendar and season history."},
  {id:"serie-a",name:"Serie A",country:"Italy",kind:"League",group:"Leagues",season:"2026/27",code:"SA",accent:"#70a8ff",description:"Italian top flight · clubs, standings, match calendar and season history."},
  {id:"bundesliga",name:"Bundesliga",country:"Germany",kind:"League",group:"Leagues",season:"2026/27",code:"BL",accent:"#ff6e72",description:"German top flight · clubs, standings, match calendar and season history."},
  {id:"ekstraklasa",name:"Ekstraklasa",country:"Poland",kind:"League",group:"Leagues",season:"2026",code:"EK",accent:"#f4f4f4",description:"Polish top flight · clubs, standings, match calendar and season history."},
  {id:"champions-league",name:"UEFA Champions League",country:"Europe",kind:"Continental cup",group:"UEFA Competitions",season:"2026/27",code:"UCL",accent:"#9f91ff",description:"Europe's premier club competition · league phase, knockout rounds and finals."},
  {id:"europa-league",name:"UEFA Europa League",country:"Europe",kind:"Continental cup",group:"UEFA Competitions",season:"2026/27",code:"UEL",accent:"#ffad69",description:"European club competition · league phase, knockout rounds and finals."},
  {id:"conference-league",name:"UEFA Conference League",country:"Europe",kind:"Continental cup",group:"UEFA Competitions",season:"2026/27",code:"UECL",accent:"#8fd369",description:"European club competition · league phase, knockout rounds and finals."},
  {id:"fifa-world-cup",name:"FIFA World Cup",country:"International",kind:"National teams",group:"International Football",season:"2026",code:"WC",accent:"#77d9be",description:"Men's national-team world championship and tournament history."},
  {id:"uefa-euro",name:"UEFA European Championship",country:"Europe",kind:"National teams",group:"International Football",season:"2028",code:"EURO",accent:"#78a9ff",description:"European national-team championship and qualifying history."},
  {id:"nations-league",name:"UEFA Nations League",country:"Europe",kind:"National teams",group:"International Football",season:"2026/27",code:"UNL",accent:"#d1a3ff",description:"UEFA national-team league phases, finals and promotion/relegation."},
  {id:"world-cup-qualifiers",name:"World Cup Qualifiers",country:"International",kind:"National teams",group:"International Football",season:"2026",code:"WCQ",accent:"#91c5d7",description:"Regional qualification paths for the FIFA World Cup."},
  {id:"copa-america",name:"Copa América",country:"South America",kind:"National teams",group:"International Football",season:"2028",code:"CA",accent:"#87d3a0",description:"South American national-team championship and historical results."},
  {id:"afcon",name:"Africa Cup of Nations",country:"Africa",kind:"National teams",group:"International Football",season:"2027",code:"AFCON",accent:"#e0c56e",description:"African national-team championship and qualifying history."},
  {id:"asian-cup",name:"AFC Asian Cup",country:"Asia",kind:"National teams",group:"International Football",season:"2027",code:"AFC",accent:"#e89278",description:"Asian national-team championship and qualifying history."},
  {id:"concacaf-gold-cup",name:"CONCACAF Gold Cup",country:"North & Central America",kind:"National teams",group:"International Football",season:"2027",code:"GC",accent:"#f2d16b",description:"North American, Central American and Caribbean championship."},
  {id:"fa-cup",name:"FA Cup",country:"England",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"FA",accent:"#83d5bd",description:"England's national knockout cup."},
  {id:"efl-cup",name:"EFL Cup",country:"England",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"EFL",accent:"#66aaff",description:"England's league cup knockout competition."},
  {id:"community-shield",name:"FA Community Shield",country:"England",kind:"Super cup",group:"Domestic Cups",season:"2026",code:"CS",accent:"#d9f2e9",description:"English season-opening super cup."},
  {id:"coupe-de-france",name:"Coupe de France",country:"France",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"CDF",accent:"#6dc4ed",description:"France's national knockout cup."},
  {id:"trophee-champions",name:"Trophée des Champions",country:"France",kind:"Super cup",group:"Domestic Cups",season:"2026",code:"TDC",accent:"#a8d6ff",description:"French season-opening super cup."},
  {id:"copa-del-rey",name:"Copa del Rey",country:"Spain",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"CDR",accent:"#ff9a83",description:"Spain's national knockout cup."},
  {id:"supercopa-espana",name:"Supercopa de España",country:"Spain",kind:"Super cup",group:"Domestic Cups",season:"2027",code:"SDE",accent:"#ffc18d",description:"Spanish super cup."},
  {id:"coppa-italia",name:"Coppa Italia",country:"Italy",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"CI",accent:"#84b0ff",description:"Italy's national knockout cup."},
  {id:"supercoppa-italiana",name:"Supercoppa Italiana",country:"Italy",kind:"Super cup",group:"Domestic Cups",season:"2026/27",code:"SI",accent:"#b5d4ff",description:"Italian super cup."},
  {id:"dfb-pokal",name:"DFB-Pokal",country:"Germany",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"DFB",accent:"#ff8989",description:"Germany's national knockout cup."},
  {id:"dfl-supercup",name:"DFL-Supercup",country:"Germany",kind:"Super cup",group:"Domestic Cups",season:"2026",code:"DFL",accent:"#ffc1c1",description:"German season-opening super cup."},
  {id:"puchar-polski",name:"Puchar Polski",country:"Poland",kind:"Domestic cup",group:"Domestic Cups",season:"2026/27",code:"PP",accent:"#f3f4f4",description:"Poland's national knockout cup."},
  {id:"superpuchar-polski",name:"Superpuchar Polski",country:"Poland",kind:"Super cup",group:"Domestic Cups",season:"2026",code:"SP",accent:"#d8e8e2",description:"Polish super cup."}
];

const GROUPS = ["Leagues", "UEFA Competitions", "International Football", "Domestic Cups"];
const FILTERS = ["All", ...GROUPS];
const TABS = ["Overview", "Standings", "Fixtures & Results", "Teams", "Players", "Records"];
const VIEW_TITLES = {teams:"Teams",players:"Players",calendar:"Calendar",records:"Records"};
const DATA_MESSAGE = "Competition pages are ready, but football data is not connected yet. Results, standings and statistics are intentionally unavailable until a verified data source is configured.";

function byId(id){return document.getElementById(id)}
function esc(value){return String(value).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
function competitionUrl(item){return `./competition.html?id=${encodeURIComponent(item.id)}`}
function renderCard(item){return `<a class="competition-card" href="${competitionUrl(item)}" style="--card-accent:${esc(item.accent)}"><div class="card-top"><span class="competition-badge" aria-hidden="true">${esc(item.code)}</span><span class="card-category">${esc(item.kind)}</span><span class="card-arrow" aria-hidden="true">↗</span></div><h3>${esc(item.name)}</h3><p class="card-detail">${esc(item.country)} <span>·</span> ${esc(item.season)}</p><p class="card-description">${esc(item.description)}</p></a>`}

function initDirectory(){
  const root=byId("competitionGroups");
  if(!root)return;
  let active="All",query="";
  const filters=byId("filterRow"),search=byId("competitionSearch"),empty=byId("emptyState");
  filters.innerHTML=FILTERS.map((name,i)=>`<button class="filter-chip${i===0?" active":""}" type="button" aria-pressed="${i===0}" data-filter="${esc(name)}">${esc(name)}</button>`).join("");
  function draw(){
    const matches=COMPETITIONS.filter(item=>(active==="All"||item.group===active)&&`${item.name} ${item.country} ${item.kind}`.toLowerCase().includes(query));
    root.innerHTML=GROUPS.map(group=>{const items=matches.filter(item=>item.group===group);if(!items.length)return "";const desc=group==="Leagues"?"Six top-flight leagues from the countries in your plan.":group==="UEFA Competitions"?"The three major UEFA club competitions.":group==="International Football"?"Major national-team tournaments and qualification.":"Main national cups and super cups for the six selected countries.";return `<section class="competition-group"><div class="section-heading group-heading"><div><h2>${esc(group)}</h2><p>${esc(desc)}</p></div><span class="count-pill">${items.length} ${items.length===1?"competition":"competitions"}</span></div><div class="competition-grid">${items.map(renderCard).join("")}</div></section>`}).join("");
    empty.hidden=matches.length>0;
  }
  filters.addEventListener("click",event=>{const btn=event.target.closest("[data-filter]");if(!btn)return;active=btn.dataset.filter;filters.querySelectorAll(".filter-chip").forEach(chip=>{const selected=chip===btn;chip.classList.toggle("active",selected);chip.setAttribute("aria-pressed",String(selected))});draw()});
  search.addEventListener("input",()=>{query=search.value.trim().toLowerCase();draw()});
  draw();
}

function initCompetitionPage(){
  const hero=byId("competitionHero"),panel=byId("competitionPanel"),tabs=byId("competitionTabs");
  if(!hero||!panel||!tabs)return;
  const params=new URLSearchParams(location.search),id=params.get("id"),view=params.get("view"),item=COMPETITIONS.find(comp=>comp.id===id);
  if(!item){
    const title=VIEW_TITLES[view];
    hero.innerHTML=title?`<div class="eyebrow">Football statistics directory</div><h1 class="title">${esc(title)} <span>hub.</span></h1><p class="subtitle">Browse ${esc(title.toLowerCase())} across the competitions directory as verified data becomes available.</p><a class="button-link" href="./index.html">Choose a competition →</a>`:`<div class="eyebrow">Competition not found</div><h1 class="title">Choose a <span>competition.</span></h1><a class="button-link" href="./index.html">Browse competitions →</a>`;
    tabs.innerHTML="";panel.innerHTML=`<div class="unavailable"><span class="unavailable-icon">◷</span><h2>Data connection pending</h2><p>${esc(DATA_MESSAGE)}</p><a class="text-link" href="./health.html">See data status →</a></div>`;return;
  }
  document.title=`${item.name} | Football & Soccer Stats`;
  hero.innerHTML=`<div class="competition-kicker"><span>${esc(item.group)}</span><span>·</span><span>${esc(item.country)}</span></div><div class="competition-title-row"><span class="competition-crest" style="--card-accent:${esc(item.accent)}">${esc(item.code)}</span><div><h1>${esc(item.name)}</h1><p>${esc(item.description)}</p></div></div><div class="season-row"><span class="season-label">Season</span><span class="season-select-static">${esc(item.season)} <span aria-hidden="true">⌄</span></span><span class="availability-pill"><i class="status-dot pending"></i> Data unavailable</span></div>`;
  tabs.innerHTML=TABS.map((name,i)=>`<button class="tab-button${i===0?" active":""}" role="tab" aria-selected="${i===0}" data-tab="${esc(name)}">${esc(name)}</button>`).join("");
  function show(tab){const copy={"Overview":"Competition overview","Standings":"Standings & table","Fixtures & Results":"Fixtures & results","Teams":"Teams","Players":"Players","Records":"Competition records"};panel.innerHTML=`<div class="panel-heading"><div><div class="eyebrow">${esc(item.name)} · ${esc(item.season)}</div><h2>${esc(copy[tab]||tab)}</h2></div><span class="availability-pill"><i class="status-dot pending"></i> Not connected</span></div><div class="unavailable"><span class="unavailable-icon">◷</span><h3>Verified data is not available yet</h3><p>${esc(DATA_MESSAGE)}</p><a class="text-link" href="./health.html">Check provider setup →</a></div>`}
  tabs.addEventListener("click",event=>{const btn=event.target.closest("[data-tab]");if(!btn)return;tabs.querySelectorAll(".tab-button").forEach(tab=>{const selected=tab===btn;tab.classList.toggle("active",selected);tab.setAttribute("aria-selected",String(selected))});show(btn.dataset.tab)});
  show("Overview");
}

initDirectory();
initCompetitionPage();
