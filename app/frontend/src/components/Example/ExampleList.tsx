import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "How does the solution ensure data security and compliance with industry regulations?",
        value: "How does the solution ensure data security and compliance with industry regulations?"
    },
    { text: "How would the system handle images with incorrect rotation?", value: "How would the system handle images with incorrect rotation?" },
    {
        text: "Does the solution  provide custom clean up profiles for certain document types?",
        value: "Does the solution  provide custom clean up profiles for certain document types?"
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
