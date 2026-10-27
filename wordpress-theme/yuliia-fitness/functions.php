<?php
/**
 * Theme setup, dynamic blocks, editor, and protected booking form.
 *
 * @package Yuliia_Fitness
 */
defined( 'ABSPATH' ) || exit;

const YULIIA_VERSION = '0.1.0';

add_action( 'after_setup_theme', function () {
    load_theme_textdomain( 'yuliia-fitness', get_template_directory() . '/languages' );
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', array( 'search-form', 'comment-form', 'gallery', 'caption', 'style', 'script' ) );
    add_theme_support( 'responsive-embeds' );
    add_theme_support( 'wp-block-styles' );
    add_theme_support( 'editor-styles' );
    add_editor_style( 'assets/css/editor.css' );
    register_nav_menus( array( 'primary' => __( 'Головне меню', 'yuliia-fitness' ) ) );
} );

add_action( 'wp_enqueue_scripts', function () {
    wp_enqueue_style( 'yuliia-fonts', 'https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=Manrope:wght@200..800&display=swap', array(), null );
    wp_enqueue_style( 'yuliia-style', get_theme_file_uri( '/assets/css/site.css' ), array( 'yuliia-fonts' ), YULIIA_VERSION );
    wp_enqueue_style( 'yuliia-hero', get_theme_file_uri( '/assets/css/hero.css' ), array( 'yuliia-style' ), YULIIA_VERSION );
    wp_enqueue_style( 'yuliia-mission', get_theme_file_uri( '/assets/css/mission.css' ), array( 'yuliia-hero' ), YULIIA_VERSION );
    wp_enqueue_style( 'yuliia-motion', get_theme_file_uri( '/assets/css/motion.css' ), array( 'yuliia-mission' ), YULIIA_VERSION );
    wp_enqueue_script( 'yuliia-ui', get_theme_file_uri( '/assets/js/site.js' ), array(), YULIIA_VERSION, array( 'in_footer' => true, 'strategy' => 'defer' ) );
} );

function yuliia_schema(): array {
    static $schema = null;
    if ( null === $schema ) {
        $data = file_get_contents( get_theme_file_path( '/inc/sections.json' ) );
        $decoded = is_string( $data ) ? json_decode( $data, true ) : null;
        $schema = is_array( $decoded ) ? $decoded : array();
    }
    return $schema;
}

function yuliia_field( array $fields, string $key, string $fallback ): string {
    if ( ! isset( $fields[ $key ] ) || ! is_string( $fields[ $key ] ) ) {
        return $fallback;
    }
    return $fields[ $key ];
}

function yuliia_image( array $fields, string $key, string $fallback ): string {
    $url = yuliia_field( $fields, $key, '' );
    if ( '' !== $url && preg_match( '~^(https?://|/)~i', $url ) ) {
        return $url;
    }
    return get_theme_file_uri( '/' . ltrim( $fallback, '/' ) );
}

/** Render menu locations using the menu editor; fall back to approved anchors. */
function yuliia_nav( string $location, string $class, string $label, string $id = '', bool $hidden = false ): void {
    $id_attribute = '' !== $id ? ' id="' . esc_attr( $id ) . '"' : '';
    echo '<nav' . $id_attribute . ' class="' . esc_attr( $class ) . '" aria-label="' . esc_attr( $label ) . '"' . ( $hidden ? ' hidden' : '' ) . '>';
    if ( has_nav_menu( $location ) ) {
        wp_nav_menu( array(
            'theme_location' => $location, 'container' => false, 'depth' => 1,
            'items_wrap' => '<ul class="yf-nav-items">%3$s</ul>',
            'fallback_cb' => false,
        ) );
    } else {
        $links = array(
            'Про мене' => 'about', 'Програми' => 'formats', 'Харчування' => 'nutrition',
            'Результати' => 'results', 'Відгуки' => 'reviews', 'FAQ' => 'faq',
        );
        foreach ( $links as $name => $anchor ) {
            echo '<a href="' . esc_url( home_url( '/#' . $anchor ) ) . '">' . esc_html( $name ) . '</a>';
        }
    }
    echo '</nav>';
}

function yuliia_render_section( array $attributes ): string {
    $name = isset( $attributes['section'] ) ? sanitize_key( $attributes['section'] ) : '';
    if ( ! array_key_exists( $name, yuliia_schema() ) ) {
        return '';
    }
    $fields = ( isset( $attributes['fields'] ) && is_array( $attributes['fields'] ) ) ? $attributes['fields'] : array();
    ob_start();
    require get_theme_file_path( '/sections/' . $name . '.php' );
    return (string) ob_get_clean();
}

add_action( 'init', function () {
    wp_register_script(
        'yuliia-editor',
        get_theme_file_uri( '/assets/js/editor.js' ),
        array( 'wp-blocks', 'wp-element', 'wp-components', 'wp-block-editor', 'wp-i18n' ),
        YULIIA_VERSION,
        true
    );
    wp_add_inline_script(
        'yuliia-editor',
        'window.YuliiaBlockConfig = ' . wp_json_encode( array(
            'schema' => yuliia_schema(),
            'themeUrl' => get_template_directory_uri(),
        ) ) . ';',
        'before'
    );
    register_block_type( get_theme_file_path( '/blocks/landing-section' ), array(
        'editor_script' => 'yuliia-editor',
        'render_callback' => 'yuliia_render_section',
    ) );
} );

/** Install seed blocks on a fresh site, never overwrite a configured homepage. */
add_action( 'after_switch_theme', function () {
    if ( (int) get_option( 'page_on_front' ) > 0 ) {
        return;
    }
    $existing = get_page_by_path( 'golovna' );
    if ( $existing instanceof WP_Post ) {
        return;
    }
    $blocks = array();
    foreach ( array_keys( yuliia_schema() ) as $section ) {
        $blocks[] = serialize_block( array(
            'blockName' => 'yuliia/section',
            'attrs' => array( 'section' => $section ),
            'innerBlocks' => array(),
            'innerHTML' => '',
            'innerContent' => array(),
        ) );
    }
    $id = wp_insert_post( array(
        'post_title' => 'Головна',
        'post_name' => 'golovna',
        'post_status' => 'publish',
        'post_type' => 'page',
        'post_content' => implode( '', $blocks ),
    ), true );
    if ( ! is_wp_error( $id ) ) {
        update_option( 'show_on_front', 'page' );
        update_option( 'page_on_front', $id );
    }
} );

add_action( 'customize_register', function ( WP_Customize_Manager $wp_customize ) {
    $wp_customize->add_section( 'yuliia_settings', array(
        'title' => 'Yuliia: налаштування сайту', 'priority' => 40,
    ) );
    $wp_customize->add_setting( 'yuliia_video_url', array(
        'default' => '', 'sanitize_callback' => 'esc_url_raw',
    ) );
    $wp_customize->add_control( 'yuliia_video_url', array(
        'label' => 'URL MP4-відео (показувати кнопку лише за наявності URL)',
        'section' => 'yuliia_settings', 'type' => 'url',
    ) );
    $wp_customize->add_setting( 'yuliia_content_verified', array(
        'default' => false, 'sanitize_callback' => 'rest_sanitize_boolean',
    ) );
    $wp_customize->add_control( 'yuliia_content_verified', array(
        'label' => 'Підтверджені фото, цифри, тарифи й відгуки',
        'description' => 'Увімкнути лише після перевірки всього демонстраційного контенту.',
        'section' => 'yuliia_settings', 'type' => 'checkbox',
    ) );
} );

add_action( 'admin_post_nopriv_yuliia_contact', 'yuliia_handle_contact' );
add_action( 'admin_post_yuliia_contact', 'yuliia_handle_contact' );
function yuliia_handle_contact(): void {
    $redirect = home_url( '/#contact' );
    $nonce = isset( $_POST['yf_nonce'] ) ? sanitize_text_field( wp_unslash( $_POST['yf_nonce'] ) ) : '';
    if ( ! wp_verify_nonce( $nonce, 'yuliia_contact' ) ) {
        wp_die( esc_html__( 'Термін дії форми минув. Оновіть сторінку.', 'yuliia-fitness' ), '', array( 'response' => 403 ) );
    }
    if ( ! empty( $_POST['website'] ) ) {
        wp_safe_redirect( add_query_arg( 'yf_status', 'ok', $redirect ) );
        exit;
    }
    $name = isset( $_POST['name'] ) ? sanitize_text_field( wp_unslash( $_POST['name'] ) ) : '';
    $email = isset( $_POST['email'] ) ? sanitize_email( wp_unslash( $_POST['email'] ) ) : '';
    $message = isset( $_POST['message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['message'] ) ) : '';
    $consent = ! empty( $_POST['consent'] );
    if ( ! $consent || '' === $name || strlen( $name ) > 160 || ! is_email( $email ) || strlen( $message ) < 10 || strlen( $message ) > 5000 ) {
        wp_safe_redirect( add_query_arg( 'yf_status', 'invalid', $redirect ) );
        exit;
    }
    $ip = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
    $rate_key = 'yf_form_' . hash_hmac( 'sha256', $ip, wp_salt() );
    if ( get_transient( $rate_key ) ) {
        wp_safe_redirect( add_query_arg( 'yf_status', 'rate', $redirect ) );
        exit;
    }
    set_transient( $rate_key, 1, MINUTE_IN_SECONDS );
    $subject = sprintf( '[Yuliia] Нова заявка — %s', $name );
    $body = "Ім’я: " . $name . "\nEmail: " . $email . "\n\n" . $message;
    $headers = array( 'Reply-To: ' . $email );
    $sent = wp_mail( get_option( 'admin_email' ), $subject, $body, $headers );
    wp_safe_redirect( add_query_arg( 'yf_status', $sent ? 'ok' : 'error', $redirect ) );
    exit;
}
