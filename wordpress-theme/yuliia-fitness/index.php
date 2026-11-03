<?php defined( 'ABSPATH' ) || exit; get_header(); ?>
<main id="main-content" class="wrap section light-section">
<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
<article <?php post_class(); ?>><h1><?php the_title(); ?></h1><?php the_content(); ?></article>
<?php endwhile; the_posts_pagination(); else: ?>
<p>Записів поки немає.</p>
<?php endif; ?>
</main><?php get_footer(); ?>
