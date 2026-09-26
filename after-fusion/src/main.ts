// SPDX-License-Identifier: MIT OR Apache-2.0
const load = document.querySelector<HTMLButtonElement>('#load')!;
const statusElement = document.querySelector<HTMLElement>('#status')!;
load.addEventListener('click', async () => {
  load.disabled = true;
  statusElement.textContent = 'Loading the prepared model and geometry…';
  try {
    const probe = document.createElement('canvas');
    const context = probe.getContext('webgl2');
    if (!context) throw new Error('WebGL2 is unavailable. Use the poster and inspect the prepared JSON files.');
    context.getExtension('WEBGL_lose_context')?.loseContext();
    const { start } = await import('./viewer.ts');
    await start();
    load.hidden = true;
    document.querySelector<HTMLElement>('#poster')!.hidden = true;
    document.querySelector<HTMLElement>('#controls')!.hidden = false;
    statusElement.textContent = 'Ready. Choose a view and scrub its physical model time.';
  } catch (error) {
    statusElement.textContent = error instanceof Error ? error.message : 'The viewer could not load.';
    load.disabled = false;
  }
});
