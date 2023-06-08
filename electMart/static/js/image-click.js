$(document).ready(function(){
    $('.thumb a').click(function(e){
        e.preventDefault();
        mainImgURL = $('mainImage img').attr('href')
        $('.mainImage img').attr('src', $(this).attr('href'));
        $(this).attr('src', mainImgURL)
    })
})