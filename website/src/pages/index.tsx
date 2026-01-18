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
        <img
          src="/betamax/img/betamax-logo.png"
          alt="Betamax Logo"
          className={styles.heroLogo}
        />
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
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
        <div className={styles.heroDemo}>
          <img
            src="/betamax/img/gradient_wave.gif"
            alt="Betamax animated demo"
            className={styles.heroDemoGif}
          />
          <p className={styles.heroDemoCaption}>Animated ASCII art recorded with Betamax</p>
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
  {
    title: 'Precise Frame Control',
    icon: 'icon-video',
    description: (
      <>
        Capture frames exactly when you want. Create smooth, professional
        GIF recordings with explicit control over every frame.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={clsx('col col--3')}>
      <div className={styles.featureCard}>
        <i className={clsx(icon, styles.featureIcon)} />
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
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
{`# Inline keys
betamax "vim /tmp/test.txt" -- \\
  i "hello world" Escape ":wq" Enter

# From keys file
betamax "myapp" -f capture.keys

# Quick screenshot
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
            <div className="row">
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
