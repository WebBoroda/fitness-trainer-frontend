<?php
/**
 * Integration assertions, run via WP-CLI eval-file in a fresh WordPress instance.
 */
if ( ! function_exists( 'parse_blocks' ) ) {
    throw new RuntimeException( 'WordPress was not loaded.' );
}
$id = (int) get_option( 'page_on_front' );
if ( ! $id ) {
    throw new RuntimeException( 'Theme did not create a homepage.' );
}
$post = get_post( $id );
if ( ! $post || 'page' !== $post->post_type ) {
    throw new RuntimeException( 'Homepage is not a WordPress Page.' );
}
$blocks = parse_blocks( $post->post_content );
if ( 11 !== count( $blocks ) ) {
    throw new RuntimeException( 'Expected 11 Gutenberg section blocks, got ' . count( $blocks ) );
}
foreach ( $blocks as $block ) {
    if ( 'yuliia/section' !== $block['blockName'] ) {
        throw new RuntimeException( 'Wrong block type.' );
    }
}
$html = do_blocks( $post->post_content );
if ( false === strpos( $html, 'СИЛЬНІША' ) || false === strpos( $html, 'id="formats"' ) ) {
    throw new RuntimeException( 'Server-rendered frontend missing content.' );
}
if ( false !== strpos( $html, 'example.invalid' ) || false !== strpos( $html, 'data:image/' ) ) {
    throw new RuntimeException( 'Placeholder or embedded media leaked into rendered HTML.' );
}
$blocks[0]['attrs']['fields']['t1'] = 'ТЕСТ РЕДАГУВАННЯ';
$saved = serialize_blocks( $blocks );
$update = wp_update_post( array( 'ID' => $id, 'post_content' => $saved ), true );
if ( is_wp_error( $update ) ) {
    throw new RuntimeException( 'Failed saving block attributes.' );
}
$rendered_again = do_blocks( get_post( $id )->post_content );
if ( false === strpos( $rendered_again, 'ТЕСТ РЕДАГУВАННЯ' ) ) {
    throw new RuntimeException( 'Gutenberg field change not reflected in frontend.' );
}
echo "PASS: WordPress install, activation, 11 blocks, dynamic rendering, saved attribute updates.\n";
