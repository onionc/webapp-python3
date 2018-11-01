
function showPage(page){
    s = ''
    index = page.page_index
    if (page.has_prev)
        s+="<a href='?page="+(index-1)+"'>prev</a>"
    s+=index    
    if (page.has_next)
        s+="<a href='?page="+(index+1)+"'>next</a>"
    return s
}
