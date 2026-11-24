const toggle=document.getElementById('themeToggle');
if(localStorage.getItem('edutrack-theme')==='dark')document.body.classList.add('dark');
if(toggle)toggle.addEventListener('click',()=>{document.body.classList.toggle('dark');localStorage.setItem('edutrack-theme',document.body.classList.contains('dark')?'dark':'light')});
const search=document.getElementById('tableSearch');
if(search)search.addEventListener('input',()=>{const q=search.value.toLowerCase();document.querySelectorAll('#studentTable tbody tr').forEach(row=>row.style.display=row.innerText.toLowerCase().includes(q)?'':'none')});
