<?php defined( 'ABSPATH' ) || exit;
$status = isset( $_GET['yf_status'] ) ? sanitize_key( wp_unslash( $_GET['yf_status'] ) ) : '';
$messages = array(
    'ok' => 'Дякуємо! Заявку прийнято для надсилання.',
    'invalid' => 'Перевірте правильність заповнення полів і згоду.',
    'rate' => 'Повторіть спробу трохи пізніше.',
    'error' => 'Не вдалося надіслати лист. Спробуйте ще раз.',
);
?>
<section class="yf-contact" id="contact" aria-labelledby="yf-contact-heading">
<div class="wrap">
<span class="eyebrow dark-pill">ЗАПИС НА КОНСУЛЬТАЦІЮ</span>
<h2 id="yf-contact-heading">ЗРОБИ ПЕРШИЙ КРОК</h2>
<p>Залиш контакти та коротко розкажи про свою мету. Відповідь надійде електронною поштою.</p>
<?php if ( isset( $messages[ $status ] ) ) : ?>
<p class="yf-contact-message" role="status"><?php echo esc_html( $messages[ $status ] ); ?></p>
<?php endif; ?>
<form action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" method="post">
<input type="hidden" name="action" value="yuliia_contact">
<?php wp_nonce_field( 'yuliia_contact', 'yf_nonce' ); ?>
<label>Ім’я <input type="text" name="name" autocomplete="name" maxlength="160" required></label>
<label>Email <input type="email" name="email" autocomplete="email" required></label>
<label class="hp" aria-hidden="true">Не заповнювати <input name="website" tabindex="-1" autocomplete="off"></label>
<label class="full">Твоя мета <textarea name="message" rows="4" minlength="10" maxlength="5000" required></textarea></label>
<label class="full consent"><input type="checkbox" name="consent" value="1" required><span>Погоджуюся на використання даних для відповіді на звернення.</span></label>
<?php if ( get_privacy_policy_url() ) : ?>
<p class="full"><a href="<?php echo esc_url( get_privacy_policy_url() ); ?>">Політика конфіденційності</a></p>
<?php endif; ?>
<button type="submit" class="btn fill">Надіслати заявку <span class="arrow">→</span></button>
</form>
</div>
</section>
