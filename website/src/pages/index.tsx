import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <div className={styles.heroHeader}>
          <img
            src="/betamax/img/betamax-logo-fuzzy.png"
            alt="Betamax Logo"
            className={styles.heroLogo}
          />
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <div className={styles.heroCta}>
            <div className={styles.buttons}>
              <Link
                className="button button--primary button--lg"
                to="/docs/intro">
                Get Started
              </Link>
              <Link
                className="button button--secondary button--lg"
                href="https://github.com/marcus/betamax">
                View on GitHub
              </Link>
            </div>
            <p className={styles.heroNote}>Works with tmux • No custom terminal needed</p>
          </div>
          <div className={styles.heroDemo}>
            <img
              src="/betamax/img/gradient_wave.gif"
              alt="Betamax animated demo"
              className={styles.heroDemoGif}
            />
            <p className={styles.heroDemoCaption}>Animated ASCII art recorded with Betamax</p>
          </div>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Interactive Recording',
    icon: 'icon-circle-dot',
    description: (
      <>
        Record your terminal sessions with <code>betamax record</code>. Captures
        keystrokes with precise timing for perfect playback.
      </>
    ),
  },
  {
    title: 'Screenshot Capture',
    icon: 'icon-camera',
    description: (
      <>
        Capture TUI screenshots with <code>betamax capture</code>. Press a hotkey
        anytime during vim, htop, or any TUI to take a PNG.
      </>
    ),
  },
  {
    title: 'Multiple Output Formats',
    icon: 'icon-layers',
    description: (
      <>
        Export to TXT, HTML, PNG, or animated GIF. Perfect for documentation,
        READMEs, and demos.
      </>
    ),
  },
  {
    title: 'Declarative Keys Files',
    icon: 'icon-file-text',
    description: (
      <>
        Self-describing scripts with inline settings. Version control your
        terminal recordings alongside your code.
      </>
    ),
  },
  {
    title: 'tmux-based Headless Operation',
    icon: 'icon-terminal',
    description: (
      <>
        Uses tmux under the hood. No custom terminal emulator needed. Works
        in CI/CD pipelines and headless environments.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={styles.featureCard}>
      <div className={styles.featureIconWrapper}>
        <i className={clsx(icon, styles.featureIcon)} />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function QuickStart() {
  return (
    <section className={styles.quickStart}>
      <div className="container">
        <Heading as="h2">Quick Start</Heading>
        <div className="row">
          <div className="col col--6">
            <h3>Installation</h3>
            <CodeBlock language="bash">
{`# Clone and add to PATH
git clone https://github.com/marcus/betamax
export PATH="$PWD/betamax:$PATH"

# Install dependencies (macOS)
brew install tmux
brew install homeport/tap/termshot  # for PNG
brew install ffmpeg                  # for GIF`}
            </CodeBlock>
          </div>
          <div className="col col--6">
            <h3>Basic Usage</h3>
            <CodeBlock language="bash">
{`# Capture TUI screenshots interactively
betamax capture vim myfile.py  # Ctrl+G to screenshot

# Record your terminal session
betamax record -o demo.keys vim test.txt

# Play back with GIF output
betamax "vim test.txt" -f demo.keys

# Or use inline keys directly
betamax "htop" -- @sleep:1000 @capture:htop.png q`}
            </CodeBlock>
          </div>
        </div>
        <div className={styles.quickStartDemo}>
          <img
            src="/betamax/img/demos/betamax_inline.gif"
            alt="Betamax inline usage demo"
            className={styles.quickStartGif}
          />
        </div>
      </div>
    </section>
  );
}

function OutputFormats() {
  return (
    <section className={styles.outputFormats}>
      <div className="container">
        <Heading as="h2">Output Formats</Heading>
        <div className={styles.formatGrid}>
          <div className={styles.formatCard}>
            <code>.txt</code>
            <span>Raw text with ANSI codes</span>
          </div>
          <div className={styles.formatCard}>
            <code>.html</code>
            <span>Styled HTML with colors</span>
          </div>
          <div className={styles.formatCard}>
            <code>.png</code>
            <span>Screenshot image</span>
          </div>
          <div className={styles.formatCard}>
            <code>.gif</code>
            <span>Animated recording</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Terminal Session Recorder"
      description="Terminal session recorder for TUI applications. Uses tmux for headless operation.">
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className={styles.featureGrid}>
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
        <QuickStart />
        <OutputFormats />
      </main>
    </Layout>
  );
}
