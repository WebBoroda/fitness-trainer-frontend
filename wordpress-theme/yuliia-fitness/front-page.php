<?php
defined( 'ABSPATH' ) || exit;
get_header();
?>
<main id="main-content">
<?php
while ( have_posts() ) {
    the_post();
    the_content();
}
get_template_part( 'parts/contact' );
?>
</main>
<?php get_footer(); ?>
